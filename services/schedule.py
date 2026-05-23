from services.auth import ModeusAuth
from utils.headers import get_auth_headers
import httpx
import json
from datetime import datetime, timedelta
import asyncio
import time
from database.mmap_db import MmapDB

class ModeusSchedule:
    def __init__(self, auth: ModeusAuth):
        self.auth = auth

    async def _fetch_schedule(self, date_start, date_end, user_id):
        """Асинхронное получение данных из API с отладкой."""
        time_min = f"{date_start}T00:00:00+05:00"
        time_max = f"{date_end}T23:59:59+05:00"

        data = {
            "size": 500,
            "timeMin": time_min,
            "timeMax": time_max,
            "attendeePersonId": [user_id]
        }
        headers = {
            **get_auth_headers(self.auth.bearer_token),
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd"
        }
        url = 'https://utmn.modeus.org/schedule-calendar-v2/api/calendar/events/search?tz=Asia/Tyumen'

        print(f"Fetching schedule for user_id: {user_id}, date_start: {date_start}, date_end: {date_end}")
        print(f"Computed timeMin: {time_min}, timeMax: {time_max}")
        print(f"Request headers: {json.dumps(headers, ensure_ascii=False)}")
        print(f"Request payload: {json.dumps(data, ensure_ascii=False)}")

        async with httpx.AsyncClient(http2=True) as client:
            try:
                response = await client.post(url, headers=headers, json=data)
                print(f"Response status: {response.status_code}")
                print(f"Response headers: {json.dumps(dict(response.headers), ensure_ascii=False)}")
                print(f"Response content (first 1000 chars): {response.text[:1000]}")
                response.raise_for_status()
                json_response = response.json()
                print(f"Parsed JSON response: {json.dumps(json_response, ensure_ascii=False)[:1000]}")
                return json_response['_embedded']
            except httpx.HTTPStatusError as e:
                print(f"HTTP error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Failed to fetch schedule: {str(e)}")
            except json.JSONDecodeError as e:
                print(f"JSON decode error: {str(e)} - Response content: {response.text}")
                raise Exception(f"Invalid JSON response from API: {str(e)}")
            except Exception as e:
                print(f"Unexpected error in _fetch_schedule: {str(e)}")
                raise

    async def _format_schedule(self, data):
        """Форматирование данных расписания с отладкой."""
        print(f"Formatting schedule data: {json.dumps(data, ensure_ascii=False)[:500]}")

        required_keys = ['events', 'course-unit-realizations', 'rooms', 'event-rooms']
        if not all(key in data for key in required_keys) or not all(data[key] for key in required_keys):
            print(f"Missing or empty required keys in data: {required_keys}")
            return []

        events = data['events']
        lessons = data["course-unit-realizations"]
        rooms = data["rooms"]
        event_rooms = data["event-rooms"]

        print(f"Events count: {len(events)}, Lessons count: {len(lessons)}, Rooms count: {len(rooms)}, Event-rooms count: {len(event_rooms)}")

        lesson_ids_to_names = {lesson['_links']['self']['href']: lesson['name'] for lesson in lessons}
        event_ids_to_rooms = {}
        for event_room in event_rooms:
            event_id = event_room['_links']['event']['href'].split('/')[-1]
            room_id = event_room['_links']['room']['href'].split('/')[-1]
            room = next((r for r in rooms if r['id'] == room_id), None)
            if room:
                event_ids_to_rooms[event_id] = f"{room['name']} ({room['building']['address']})"

        events.sort(key=lambda event: datetime.strptime(event['start'], '%Y-%m-%dT%H:%M:%S%z'))

        day_names_ru = {
            'Monday': 'Пн', 'Tuesday': 'Вт', 'Wednesday': 'Ср', 'Thursday': 'Чт',
            'Friday': 'Пт', 'Saturday': 'Сб', 'Sunday': 'Вс'
        }

        result = {}
        for event in events:
            start_time = datetime.strptime(event['start'], '%Y-%m-%dT%H:%M:%S%z')
            end_time = datetime.strptime(event['end'], '%Y-%m-%dT%H:%M:%S%z')

            day_label = f"{day_names_ru[start_time.strftime('%A')]} {start_time.strftime('%d.%m.%Y')}"
            time_range = f"{start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"

            lesson_id = event['_links'].get('course-unit-realization', {}).get('href')
            lesson_name = lesson_ids_to_names.get(lesson_id, "Событие") if lesson_id else event['name']
            topic_name = event['name']
            event_id = event['id']
            location = event_ids_to_rooms.get(event_id, "Онлайн")

            if day_label not in result:
                result[day_label] = []
            result[day_label].append({
                "name": lesson_name,
                "topic": topic_name,
                "start": time_range,
                "location": location
            })

        for day in result:
            result[day].sort(key=lambda x: datetime.strptime(x['start'].split(" - ")[0], "%H:%M"))

        final_result = [{"day": day, "schedule": schedule} for day, schedule in result.items()]
        final_result.sort(key=lambda x: datetime.strptime(x['day'].split(" ")[1], "%d.%m.%Y"))

        print(f"Formatted schedule: {json.dumps(final_result, ensure_ascii=False)[:500]}")
        return final_result

    async def get_schedule(self, date_start: str, date_end: str, user_id: str = None):
        """Основной метод для получения расписания с отладкой и process_time."""
        start_time = time.time()
        login = self.auth.login

        print(f"Starting get_schedule for login: {login}")
        print(f"Requested date range: {date_start} to {date_end}")

        if not user_id:
            print(f"No user_id provided, fetching profile for {login}")
            profile = await MmapDB.get_profile(login)
            if not profile or "service" not in profile:
                print(f"Profile data not found or incomplete for {login}")
                raise Exception("Profile data not found or incomplete")
            user_id = profile["service"]["personId"]
            print(f"Retrieved user_id: {user_id} from profile")
        try:
            start_dt = datetime.strptime(date_start, '%Y-%m-%d')
            end_dt = datetime.strptime(date_end, '%Y-%m-%d')
            if start_dt > end_dt:
                print(f"Error: date_start ({date_start}) is after date_end ({date_end})")
                raise ValueError("date_start must be before date_end")
        except ValueError as e:
            print(f"Invalid date format or range: {str(e)}")
            raise Exception(f"Invalid date format or range: {str(e)}")

        print(f"Checking token validity for {login}")
        is_valid = await self.auth.is_token_valid()
        print(f"Token valid: {is_valid}, Current token: {self.auth.bearer_token}")
        if not is_valid:
            print(f"Token invalid or missing, re-authenticating for {login}")
            await self.auth.authenticate()
            print(f"New token after re-auth: {self.auth.bearer_token}")
        else:
            print("Token is valid, proceeding with current token")

        print(f"Fetching schedule data for {login}")
        data = await self._fetch_schedule(date_start, date_end, user_id)
        print(f"Formatting schedule for {login}")
        schedule = await self._format_schedule(data)

        process_time = time.time() - start_time
        print(f"Schedule retrieval complete for {login}, process_time: {process_time:.3f} seconds")

        return {
            "status": "success",
            "schedule": schedule,
            "process_time": f"{process_time:.3f}"
        }