from pydantic import BaseModel
from typing import List, Optional
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from data.database.database_events import init_db, SessionLocal, EventORM
from services.event_pipeline import run_email_to_db_pipeline

app = FastAPI()

scheduler = AsyncIOScheduler(timezone="Europe/Berlin")

# Allows Vite dev server to talk to the backend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://193.196.53.179:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Data model ----
class Event(BaseModel):
    """
    Event data model representing an event with optional details.
    """
    id: int
    title: str
    start_date: str
    end_date: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    speaker: Optional[str] = None
    organizer: Optional[str] = None
    registration_needed: Optional[str] = None
    url: Optional[str] = None
    image_key: Optional[str] = None

def orm_to_pydantic(event: EventORM) -> Event:
    """
    Converts an EventORM instance to a Pydantic Event model.
    """
    return Event(
        id = event.id,
        title = event.title,
        start_date = event.start_date,
        end_date = event.end_date,
        start_time = event.start_time,
        end_time = event.end_time,
        location = event.location,
        description = event.description,
        speaker = event.speaker,
        organizer = event.organizer,
        registration_needed = event.registration_needed,
        url = event.url,
        image_key = event.image_key,
    )

@app.on_event("startup")
async def startup_event():
    print("Starting up the backend server...")

    #1) Initialize the database
    init_db()

    #2) Run pipeline once at startup to fetch initial emails
    print("Running initial email to DB pipeline...")
    run_email_to_db_pipeline()

    #3) Schedule periodic email downloads
    scheduler.add_job(
        run_email_to_db_pipeline,
        trigger = CronTrigger(hour="*/1"),  # every hour
        kwargs = {"limit": 10},
        id="email_pipeline_job",
        replace_existing = True,
    )

    scheduler.start()
    print("Scheduler started, email download job scheduled.")

@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down the backend server...")
    scheduler.shutdown()
    print("Scheduler shut down.")

# ----- WebSocket endpoint -----
@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    Protocol:
      - client connects
      - client sends text "get_events"
      - server responds with JSON list of events (from DB)
    """
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()

            if message == "get_events":
                with SessionLocal() as db:
                    rows = db.query(EventORM).all()
                    events_payload = [orm_to_pydantic(event).model_dump() for event in rows]

                await websocket.send_text(json.dumps(events_payload))
    except WebSocketDisconnect:
        pass
