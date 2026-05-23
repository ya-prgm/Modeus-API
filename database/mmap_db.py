import asyncio
import json
import mmap
import os
import secrets
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)
USERS_FILE = "users.mmap"
SESSIONS_FILE = "sessions.mmap"
PROFILES_FILE = "profiles.mmap"
GRADES_FILE = "grades.mmap"

class MmapDB:
    _users_file = None
    _sessions_file = None
    _profiles_file = None
    _grades_file = None
    _users_mmap = None
    _sessions_mmap = None
    _profiles_mmap = None
    _grades_mmap = None
    _locks = {
        "users": asyncio.Lock(),
        "sessions": asyncio.Lock(),
        "profiles": asyncio.Lock(),
        "grades": asyncio.Lock()
    }

    @classmethod
    async def init_db(cls):
        """Инициализация mmap-файлов."""
        for filepath in (USERS_FILE, SESSIONS_FILE, PROFILES_FILE, GRADES_FILE):
            if not os.path.exists(filepath):
                with open(filepath, "wb") as f:
                    f.write(b"{}")
            if filepath == USERS_FILE:
                cls._users_file = open(filepath, "r+b")
                cls._users_mmap = mmap.mmap(cls._users_file.fileno(), 0)
            elif filepath == SESSIONS_FILE:
                cls._sessions_file = open(filepath, "r+b")
                cls._sessions_mmap = mmap.mmap(cls._sessions_file.fileno(), 0)
            elif filepath == PROFILES_FILE:
                cls._profiles_file = open(filepath, "r+b")
                cls._profiles_mmap = mmap.mmap(cls._profiles_file.fileno(), 0)
            else:
                cls._grades_file = open(filepath, "r+b")
                cls._grades_mmap = mmap.mmap(cls._grades_file.fileno(), 0)

    @classmethod
    async def close_db(cls):
        """Закрытие mmap-файлов."""
        if cls._users_mmap:
            cls._users_mmap.close()
            cls._users_file.close()
        if cls._sessions_mmap:
            cls._sessions_mmap.close()
            cls._sessions_file.close()
        if cls._profiles_mmap:
            cls._profiles_mmap.close()
            cls._profiles_file.close()
        if cls._grades_mmap:
            cls._grades_mmap.close()
            cls._grades_file.close()

    @classmethod
    async def _write_data(cls, filepath, mmap_obj, file_obj, data):
        """Запись данных в файл и обновление mmap."""
        encoded_data = data.encode("utf-8")
        mmap_obj.close()
        file_obj.seek(0)
        file_obj.write(encoded_data)
        file_obj.truncate(len(encoded_data))
        file_obj.flush()
        return mmap.mmap(file_obj.fileno(), 0)

    @classmethod
    async def save_user(cls, login: str, password: str):
        token = secrets.token_urlsafe(32)
        async with cls._locks["users"]:
            cls._users_mmap.seek(0)
            users_data = cls._users_mmap.read().decode("utf-8").strip('\0')
            users = json.loads(users_data) if users_data else {}
            users[login] = {"password": password, "token": token}
            new_data = json.dumps(users, ensure_ascii=False)
            cls._users_mmap = await cls._write_data(USERS_FILE, cls._users_mmap, cls._users_file, new_data)
        logger.info(f"User {login} saved with token {token}")
        return token

    @classmethod
    async def verify_user(cls, login: str, password: str) -> bool:
        async with cls._locks["users"]:
            cls._users_mmap.seek(0)
            users_data = cls._users_mmap.read().decode("utf-8").strip('\0')
            users = json.loads(users_data) if users_data else {}
            user = users.get(login)
            return user is not None and user["password"] == password

    @classmethod
    async def get_user_by_token(cls, token: str):
        async with cls._locks["users"]:
            cls._users_mmap.seek(0)
            users_data = cls._users_mmap.read().decode("utf-8").strip('\0')
            users = json.loads(users_data) if users_data else {}
            for login, data in users.items():
                if data["token"] == token:
                    return {"login": login, "password": data["password"]}
            return None

    @classmethod
    async def save_session(cls, login: str, bearer_token: str):
        async with cls._locks["sessions"]:
            cls._sessions_mmap.seek(0)
            sessions_data = cls._sessions_mmap.read().decode("utf-8").strip('\0')
            sessions = json.loads(sessions_data) if sessions_data else {}
            sessions[login] = {
                "token": bearer_token,
                "expires_at": (datetime.now() + timedelta(minutes=55)).isoformat()
            }
            new_data = json.dumps(sessions, ensure_ascii=False)
            cls._sessions_mmap = await cls._write_data(SESSIONS_FILE, cls._sessions_mmap, cls._sessions_file, new_data)

    @classmethod
    async def get_session(cls, login: str):
        async with cls._locks["sessions"]:
            cls._sessions_mmap.seek(0)
            sessions_data = cls._sessions_mmap.read().decode("utf-8").strip('\0')
            sessions = json.loads(sessions_data) if sessions_data else {}
            session = sessions.get(login)
            if session and datetime.fromisoformat(session["expires_at"]) > datetime.now():
                return session["token"]
            return None

    @classmethod
    async def save_profile(cls, login: str, profile_data: dict):
        async with cls._locks["profiles"]:
            cls._profiles_mmap.seek(0)
            profiles_data = cls._profiles_mmap.read().decode("utf-8").strip('\0')
            profiles = json.loads(profiles_data) if profiles_data else {}
            profiles[login] = profile_data
            new_data = json.dumps(profiles, ensure_ascii=False)
            cls._profiles_mmap = await cls._write_data(PROFILES_FILE, cls._profiles_mmap, cls._profiles_file, new_data)

    @classmethod
    async def get_profile(cls, login: str):
        async with cls._locks["profiles"]:
            cls._profiles_mmap.seek(0)
            profiles_data = cls._profiles_mmap.read().decode("utf-8").strip('\0')
            profiles = json.loads(profiles_data) if profiles_data else {}
            return profiles.get(login)

    @classmethod
    async def save_grades(cls, login: str, grades_data: dict):
        """Сохранение оценок."""
        async with cls._locks["grades"]:
            cls._grades_mmap.seek(0)
            grades_stored = cls._grades_mmap.read().decode("utf-8").strip('\0')
            grades = json.loads(grades_stored) if grades_stored else {}
            grades[login] = grades_data
            new_data = json.dumps(grades, ensure_ascii=False)
            cls._grades_mmap = await cls._write_data(GRADES_FILE, cls._grades_mmap, cls._grades_file, new_data)

    @classmethod
    async def get_grades(cls, login: str):
        """Получение оценок."""
        async with cls._locks["grades"]:
            cls._grades_mmap.seek(0)
            grades_data = cls._grades_mmap.read().decode("utf-8").strip('\0')
            grades = json.loads(grades_data) if grades_data else {}
            return grades.get(login)