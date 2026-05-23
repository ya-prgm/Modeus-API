from services.auth import ModeusAuth
import json
import httpx
import logging

logger = logging.getLogger(__name__)

class SearchError(Exception):
    pass

class ModeusSearch:
    def __init__(self, auth: ModeusAuth):
        self.auth = auth

    async def search_users(self, full_name: str):
        """Поиск пользователей по ФИО с автодополнением."""
        await self.auth.ensure_valid_token()
        
        data = json.dumps({
            "fullName": full_name,
            "sort": "+fullName",
            "size": 10,
            "page": 0
        })
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Authorization": f"Bearer {self.auth.bearer_token}"
        }
        url = "https://utmn.modeus.org/schedule-calendar-v2/api/people/persons/search"

        try:
            response = await self.auth.session.post(url, headers=headers, data=data)
            response.raise_for_status()
            result = response.json()['_embedded']
            persons = []
            for person, student in zip(result.get('persons', []), result.get('students', [])):
                persons.append({
                    "fullName": person.get("fullName", ""),
                    "personId": person.get("id", ""),
                    "specialtyName": student.get("specialtyName", ""),
                    "specialtyProfile": student.get("specialtyProfile", ""),
                    "learningStartDate": student.get("learningStartDate", "")
                })
            logger.info(f"Found {len(persons)} users for query: {full_name}")
            return persons

        except httpx.HTTPStatusError as e:
            raise SearchError(f"Failed to search users: {str(e)}")
        except (json.JSONDecodeError, KeyError) as e:
            raise SearchError(f"Invalid response format: {str(e)}")