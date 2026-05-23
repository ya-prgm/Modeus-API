from fastapi import HTTPException, Response, Request
from pydantic import BaseModel
from services.auth import ModeusAuth, AuthenticationError
from services.profile import ModeusProfile, ProfileRetrievalError
from services.grades import ModeusGrades, GradesRetrievalError
from services.schedule import ModeusSchedule
from services.search import ModeusSearch, SearchError
from services.calendar import CalendarService, CalendarError
from database.mmap_db import MmapDB
import json
import time
import functools
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AuthRequest(BaseModel):
    login: str
    password: str

class TokenRequest(BaseModel):
    token: str

class ScheduleRequest(BaseModel):
    token: str
    date_start: str
    date_end: str

class SearchRequest(BaseModel):
    token: str
    full_name: str

class ScheduleByIdRequest(BaseModel):
    token: str
    date_start: str
    date_end: str
    person_id: str

class CalendarRequest(BaseModel):
    token: str
    year: int
    month: int

def measure_time(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        process_time = time.time() - start_time
        logger.info(f"Function {func.__name__} completed in {process_time:.3f} seconds")
        return result
    return wrapper

@measure_time
async def auth_validate(data: AuthRequest):
    start_time = time.time()
    modeus = ModeusAuth(data.login, data.password)
    try:
        await modeus.authenticate()
        token = await MmapDB.save_user(data.login, data.password)
        await modeus.close()
        process_time = time.time() - start_time
        response_data = {"status": "success", "token": token, "process_time": f"{process_time:.3f}"}
        return Response(
            content=json.dumps(response_data, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except AuthenticationError:
        await modeus.close()
        raise HTTPException(status_code=401, detail="Invalid login or password")

@measure_time
async def get_profile(data: TokenRequest):
    start_time = time.time()
    user = await MmapDB.get_user_by_token(data.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    auth = ModeusAuth(user["login"], user["password"])
    try:
        profile_service = ModeusProfile(auth)
        result = await profile_service.get_profile()
        await auth.close()
        process_time = time.time() - start_time
        result["process_time"] = f"{process_time:.3f}"
        return Response(
            content=json.dumps(result, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except ProfileRetrievalError as e:
        await auth.close()
        raise HTTPException(status_code=500, detail=str(e))

@measure_time
async def get_schedule(data: ScheduleRequest, request: Request):
    start_time = time.time()
    logger.info(f"Request headers: {request.headers}")
    user = await MmapDB.get_user_by_token(data.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    auth = ModeusAuth(user["login"], user["password"])
    schedule_service = ModeusSchedule(auth)
    try:
        result = await schedule_service.get_schedule((datetime.strptime(data.date_start, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d'), data.date_end)
        await auth.close()
        process_time = time.time() - start_time
        result["process_time"] = f"{process_time:.3f}"
        print('--------------------------')
        print(result)
        return Response(
            content=json.dumps(result, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        await auth.close()
        logger.error(f"Error in get_schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@measure_time
async def get_grades(data: TokenRequest):
    start_time = time.time()
    user = await MmapDB.get_user_by_token(data.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    auth = ModeusAuth(user["login"], user["password"])
    try:
        grades_service = ModeusGrades(auth)
        result = await grades_service.get_grades()
        await auth.close()
        process_time = time.time() - start_time

        response_data = {"status": "success", "grades": result, "process_time": f"{process_time:.3f}"}
        print('--------------------------')
        print(response_data)
        return Response(
            content=json.dumps(response_data, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except GradesRetrievalError as e:
        await auth.close()
        raise HTTPException(status_code=500, detail=str(e))

@measure_time
async def search_users(data: SearchRequest):
    start_time = time.time()
    user = await MmapDB.get_user_by_token(data.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    auth = ModeusAuth(user["login"], user["password"])
    try:
        search_service = ModeusSearch(auth)
        result = await search_service.search_users(data.full_name)
        await auth.close()
        process_time = time.time() - start_time
        response_data = {
            "status": "success",
            "users": result,
            "process_time": f"{process_time:.3f}"
        }
        return Response(
            content=json.dumps(response_data, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except SearchError as e:
        await auth.close()
        raise HTTPException(status_code=500, detail=str(e))

@measure_time
async def get_schedule_by_id(data: ScheduleByIdRequest):
    start_time = time.time()
    user = await MmapDB.get_user_by_token(data.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    auth = ModeusAuth(user["login"], user["password"])
    schedule_service = ModeusSchedule(auth)
    try:
        result = await schedule_service.get_schedule(data.date_start, data.date_end, data.person_id)
        await auth.close()
        process_time = time.time() - start_time
        result["process_time"] = f"{process_time:.3f}"
        return Response(
            content=json.dumps(result, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except Exception as e:
        await auth.close()
        logger.error(f"Error in get_schedule_by_id: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@measure_time
async def get_calendar(data: CalendarRequest):
    """Получение данных календаря из LMS UTMN."""
    start_time = time.time()
    user = await MmapDB.get_user_by_token(data.token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    calendar_service = CalendarService(user["login"], user["password"])
    try:
        result = await calendar_service.get_calendar(data.year, data.month)
        await calendar_service.close()
        process_time = time.time() - start_time
        response_data = {
            "status": "success",
            "calendar": result,
            "process_time": f"{process_time:.3f}"
        }
        return Response(
            content=json.dumps(response_data, ensure_ascii=False),
            media_type="application/json",
            headers={"Content-Type": "application/json; charset=utf-8"}
        )
    except CalendarError as e:
        await calendar_service.close()
        raise HTTPException(status_code=500, detail=str(e))