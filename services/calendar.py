import httpx
import json
from datetime import datetime
from database.mmap_db import MmapDB
import logging

logger = logging.getLogger(__name__)

class CalendarError(Exception):
    pass

class CalendarService:
    def __init__(self, login: str, password: str):
        self.login = login
        self.password = password
        self.wstoken = None
        self.session = httpx.AsyncClient(http2=True)
        self._headers_token = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "Host": "lms.utmn.ru",
            "Origin": "https://lxp.utmn.ru",
            "Referer": "https://lxp.utmn.ru/",
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "X-Ajax-Token": "ca019d9f91d3432125d8bb8a9b63eb919606a1dd5e79d55f4ef4d50ec2d0ea14",
            "X-Requested-With": "XMLHttpRequest"
        }
        self._headers_calendar = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
            "Host": "lms.utmn.ru",
            "Origin": "https://lxp.utmn.ru",
            "Referer": "https://lxp.utmn.ru/",
            "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
            "X-Requested-With": "XMLHttpRequest"
        }

    async def _get_token(self):
        """Получение нового токена."""
        url_token = "https://lms.utmn.ru/login/token.php"
        data_token = {
            "username": self.login,
            "password": self.password,
            "service": "test"
        }
        response = await self.session.post(url_token, json=data_token, headers=self._headers_token)
        token_data = response.json()
        self.wstoken = token_data.get("token")
        if not self.wstoken:
            raise CalendarError(f"Не удалось получить токен: {token_data}")
        await MmapDB.save_session(self.login, self.wstoken)
        logger.info(f"New token obtained for {self.login}")

    async def _ensure_valid_token(self):
        """Проверка и обновление токена, если он недействителен."""
        cached_token = await MmapDB.get_session(self.login)
        if cached_token:
            self.wstoken = cached_token
            if await self._is_token_valid():
                return
            logger.info(f"Token for {self.login} is invalid, refreshing...")
        await self._get_token()

    async def _is_token_valid(self):
        """Проверка валидности токена."""
        if not self.wstoken:
            return False
        url = "https://lms.utmn.ru/webservice/rest/server.php"
        params = {
            "wsfunction": "core_webservice_get_site_info",
            "wstoken": self.wstoken,
            "moodlewsrestformat": "json"
        }
        try:
            response = await self.session.post(url, headers=self._headers_calendar, params=params)
            data = response.json()
            if "errorcode" in data and data["errorcode"] == "invalidtoken":
                return False
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError:
            return False

    async def _fetch_calendar(self, year: int, month: int):
        """Получение данных календаря."""
        await self._ensure_valid_token()
        url_calendar = "https://lms.utmn.ru/webservice/rest/server.php"
        params_calendar = {
            "wsfunction": "core_calendar_get_calendar_monthly_view",
            "year": year,
            "month": month,
            "wstoken": self.wstoken,
            "moodlewsrestformat": "json"
        }
        response = await self.session.post(url_calendar, headers=self._headers_calendar, params=params_calendar)
        data = response.json()
        if "errorcode" in data and data["errorcode"] == "invalidtoken":
            logger.info(f"Invalid token detected for {self.login}, re-authenticating...")
            await self._get_token()
            params_calendar["wstoken"] = self.wstoken
            response = await self.session.post(url_calendar, headers=self._headers_calendar, params=params_calendar)
            data = response.json()
        response.raise_for_status()
        return data

    def _format_timestamp(self, timestamp):
        """Преобразование timestamp в читаемый формат."""
        return datetime.fromtimestamp(timestamp).strftime("%d %B %Y, %H:%M:%S")

    async def get_calendar(self, year: int, month: int):
        """Основной метод для получения календаря."""
        calendar_data = await self._fetch_calendar(year, month)
        calendar = {}
        try:
            for week in calendar_data["weeks"]:
                for day in week["days"]:
                    if day.get("hasevents"):
                        day_key = f"{day['mday']:02d}.{calendar_data['date']['mon']:02d}.{calendar_data['date']['year']}"
                        if day_key not in calendar:
                            calendar[day_key] = []
                        for event in day["events"]:
                            event_data = {
                                "name": event.get('name', 'Не указано'),
                                "full_name": event.get('popupname', 'Не указано'),
                                "course": event.get('course', {}).get('fullname', 'Не указано'),
                                "event_type": event.get('eventtype', 'Не указано'),
                                "start_time": self._format_timestamp(event.get('timestart', 0)),
                                "module": event.get('modulename', 'Не указано'),
                                "overdue": event.get('overdue', 'Не указано'),
                                "event_url": event.get('url', 'Не указано'),
                                "icon_url": event.get('icon', {}).get('iconurl', 'Не указано'),
                                "edit_url": event.get('editurl', 'Не указано'),
                                "delete_url": event.get('deleteurl', 'Не указано'),
                                "view_url": event.get('viewurl', 'Не указано'),
                                "purpose": event.get('purpose', 'Не указано'),
                                "is_last_day": event.get('islastday', 'Не указано')
                            }
                            calendar[day_key].append(event_data)
        except Exception as e:
            logger.error(f"Ошибка при обработке данных календаря: {e}")
            raise CalendarError(f"Ошибка обработки данных: {e}")
        return calendar

    async def close(self):
        """Закрытие сессии."""
        await self.session.aclose()