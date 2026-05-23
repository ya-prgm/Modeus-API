import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from database.mmap_db import MmapDB
from api.routes import auth_validate, get_profile, get_schedule, get_grades, search_users, get_schedule_by_id, get_calendar
import uvicorn
import time
import logging

logger = logging.getLogger("services.schedule")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler("schedule_debug.log")
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logging.getLogger("httpx").setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await MmapDB.init_db()
    yield
    await MmapDB.close_db()

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"Request: {request.method} {request.url.path} completed in {process_time:.3f} seconds")
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    return response

app.post("/auth")(auth_validate)
app.post("/profile")(get_profile)
app.post("/schedule")(get_schedule)
app.post("/grades")(get_grades)
app.post("/search")(search_users)
app.post("/schedule-by-id")(get_schedule_by_id)
app.post("/calendar")(get_calendar)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)