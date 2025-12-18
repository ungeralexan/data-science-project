from typing import Optional, List
import json
from pydantic import BaseModel

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from data.database.database_events import init_db, SessionLocal, MainEventORM, SubEventORM, UserLikeORM, UserGoingORM  # pylint: disable=import-error
from services.event_pipeline import run_email_to_db_pipeline  # pylint: disable=import-error
from auth.routes import auth_router  # pylint: disable=import-error
from auth.utils import get_current_user  # pylint: disable=import-error

from config import (  # pylint: disable=import-error
    CORS_ORIGINS,
    SCHEDULER_TIMEZONE,
    EMAIL_PIPELINE_CRON_HOURS,
    EMAIL_PIPELINE_DEFAULT_LIMIT,
)

# This file sets up the FastAPI application, including CORS settings,
# WebSocket endpoints, and scheduled tasks for periodic email processing.

#----- FastAPI app and scheduler -----
app = FastAPI()

# Initialize scheduler
scheduler = AsyncIOScheduler(timezone=SCHEDULER_TIMEZONE)

# Add CORS (Cross-Origin Resource Sharing) middleware
# Middleware is needed to allow frontend (running on different origin) to access backend API
app.add_middleware(
    CORSMiddleware, # Middleware class for handling CORS requests
    allow_origins=CORS_ORIGINS, # Allowed origins for CORS requests (from frontend)
    allow_credentials=True, # Allow cookies, authorization headers, etc.
    allow_methods=["*"], # Allow all HTTP methods
    allow_headers=["*"], # Allow all headers
)

# ----- Include routers -----
# Needed to include auth routes
app.include_router(auth_router)

# ----- Data model ----
class Event(BaseModel):
    """
    Event data model representing an event with optional details.
    Used for both main_events and sub_events.
    """
    id: str
    title: str
    start_date: str
    end_date: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    location: Optional[str] = None  # Kept for backward compatibility / full address string
    street: Optional[str] = None
    house_number: Optional[str] = None
    zip_code: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    room: Optional[str] = None
    floor: Optional[str] = None
    description: Optional[str] = None
    speaker: Optional[str] = None
    organizer: Optional[str] = None
    registration_needed: Optional[str] = None
    url: Optional[str] = None
    image_key: Optional[str] = None
    like_count: int = 0
    going_count: int = 0
    event_type: str = "main_event"  # "main_event" or "sub_event"
    main_event_id: Optional[str] = None  # For sub_events, reference to parent main_event
    sub_event_ids: Optional[List[str]] = None  # For main_events, list of child sub_event IDs


# ---- Utility functions -----
def main_event_orm_to_pydantic(event: MainEventORM) -> Event:
    """
    Converts a MainEventORM (SQLAlchemy ORM model) instance to a Pydantic Event model.
    """
    # sub_event_ids is stored as JSON/array in the DB but we need list for pydantic model. 
    sub_event_ids_value = event.sub_event_ids

    if isinstance(sub_event_ids_value, str):
        try:
            sub_event_ids_value = json.loads(sub_event_ids_value)
        except Exception: # pylint: disable=broad-except
            sub_event_ids_value = []

    if sub_event_ids_value is None:
        sub_event_ids_value = []

    return Event(
        id = event.id,
        title = event.title,
        start_date = event.start_date,
        end_date = event.end_date,
        start_time = event.start_time,
        end_time = event.end_time,
        location = event.location,
        street = event.street,
        house_number = event.house_number,
        zip_code = event.zip_code,
        city = event.city,
        country = event.country,
        room = event.room,
        floor = event.floor,
        description = event.description,
        speaker = event.speaker,
        organizer = event.organizer,
        registration_needed = event.registration_needed,
        url = event.url,
        image_key = event.image_key,
        like_count = event.like_count or 0,
        going_count = event.going_count or 0,
        event_type = "main_event",
        main_event_id = None,
        sub_event_ids = sub_event_ids_value,
    )


def sub_event_orm_to_pydantic(event: SubEventORM) -> Event:
    """
    Converts a SubEventORM (SQLAlchemy ORM model) instance to a Pydantic Event model.
    """
    return Event(
        id = event.id,
        title = event.title,
        start_date = event.start_date,
        end_date = event.end_date,
        start_time = event.start_time,
        end_time = event.end_time,
        location = event.location,
        street = event.street,
        house_number = event.house_number,
        zip_code = event.zip_code,
        city = event.city,
        country = event.country,
        room = event.room,
        floor = event.floor,
        description = event.description,
        speaker = event.speaker,
        organizer = event.organizer,
        registration_needed = event.registration_needed,
        url = event.url,
        image_key = event.image_key,
        like_count = event.like_count or 0,
        going_count = event.going_count or 0,
        event_type = "sub_event",
        main_event_id = event.main_event_id,
        sub_event_ids = None,
    )


# ----- Startup and shutdown events -----
@app.on_event("startup")
async def startup_event(): 

    # Startup tasks
    print("Starting up the backend server...")

    #1) Initialize the database
    init_db()

    #2) Run pipeline once at startup to fetch initial emails
    try:
        print("Running initial email to DB pipeline...")
        run_email_to_db_pipeline()
    except Exception as e: # pylint: disable=broad-except
        print(f"Error during initial pipeline run: {e}")

    #3) Schedule periodic email downloads and processing
    scheduler.add_job(
        run_email_to_db_pipeline,
        trigger = CronTrigger(hour=EMAIL_PIPELINE_CRON_HOURS),  # every 6 hours
        kwargs = {"limit": EMAIL_PIPELINE_DEFAULT_LIMIT}, # process up to 15 emails each run
        id="email_pipeline_job",
        replace_existing = True,
    )

    #4) Start the scheduler
    #scheduler.start()
    print("Scheduler started, email download job scheduled.")

# ----- Shutdown tasks -----
@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down the backend server...")
    scheduler.shutdown()
    print("Scheduler shut down.")


# ----- Event Like Endpoints -----
@app.post("/api/events/{event_type}/{event_id}/like")
async def like_event(event_id: str, event_type: str, current_user = Depends(get_current_user)):
    """Increment the like count for an event and record the user's like."""

    with SessionLocal() as db:

        # Query the appropriate table based on event_type
        if event_type == "sub_event":
            event = db.query(SubEventORM).filter(SubEventORM.id == event_id).first()
        else:
            event = db.query(MainEventORM).filter(MainEventORM.id == event_id).first()

        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Check if user already liked this event
        if event_type == "sub_event":
            existing_like = db.query(UserLikeORM).filter(
                UserLikeORM.user_id == current_user.user_id,
                UserLikeORM.sub_event_id == event_id
            ).first()
        else:
            existing_like = db.query(UserLikeORM).filter(
                UserLikeORM.user_id == current_user.user_id,
                UserLikeORM.main_event_id == event_id
            ).first()
        
        if existing_like:
            # User already liked this event, return current count
            return {"like_count": event.like_count}
        
        # Create new like record
        if event_type == "sub_event":
            new_like = UserLikeORM(user_id=current_user.user_id, sub_event_id=event_id)
        else:
            new_like = UserLikeORM(user_id=current_user.user_id, main_event_id=event_id)
        db.add(new_like)
        
        event.like_count = (event.like_count or 0) + 1
        
        db.commit()
        db.refresh(event)
        
        return {"like_count": event.like_count}


@app.post("/api/events/{event_type}/{event_id}/unlike")
async def unlike_event(event_id: str, event_type: str, current_user = Depends(get_current_user)):
    """Decrement the like count for an event and remove the user's like."""
    with SessionLocal() as db:

        # Query the appropriate table based on event_type
        if event_type == "sub_event":
            event = db.query(SubEventORM).filter(SubEventORM.id == event_id).first()
        else:
            event = db.query(MainEventORM).filter(MainEventORM.id == event_id).first()

        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Find and remove the user's like record
        if event_type == "sub_event":
            existing_like = db.query(UserLikeORM).filter(
                UserLikeORM.user_id == current_user.user_id,
                UserLikeORM.sub_event_id == event_id
            ).first()
        else:
            existing_like = db.query(UserLikeORM).filter(
                UserLikeORM.user_id == current_user.user_id,
                UserLikeORM.main_event_id == event_id
            ).first()
        
        if existing_like:
            db.delete(existing_like)
            # Ensure like_count doesn't go below 0
            event.like_count = max((event.like_count or 0) - 1, 0)
            db.commit()
            db.refresh(event)
        
        return {"like_count": event.like_count}

@app.post("/api/events/{event_type}/{event_id}/going")
async def going_event(event_id: str, event_type: str, current_user = Depends(get_current_user)):
    with SessionLocal() as db:
        if event_type == "sub_event":
            event = db.query(SubEventORM).filter(SubEventORM.id == event_id).first()
        else:
            event = db.query(MainEventORM).filter(MainEventORM.id == event_id).first()

        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")

        if event_type == "sub_event":
            existing = db.query(UserGoingORM).filter(
                UserGoingORM.user_id == current_user.user_id,
                UserGoingORM.sub_event_id == event_id
            ).first()
        else:
            existing = db.query(UserGoingORM).filter(
                UserGoingORM.user_id == current_user.user_id,
                UserGoingORM.main_event_id == event_id
            ).first()

        if existing:
            return {"going_count": event.going_count}

        new_row = UserGoingORM(
            user_id=current_user.user_id,
            sub_event_id=event_id if event_type == "sub_event" else None,
            main_event_id=event_id if event_type != "sub_event" else None,
        )
        db.add(new_row)

        event.going_count = (event.going_count or 0) + 1
        db.commit()
        db.refresh(event)
        return {"going_count": event.going_count}


@app.post("/api/events/{event_type}/{event_id}/ungoing")
async def ungoing_event(event_id: str, event_type: str, current_user = Depends(get_current_user)):
    with SessionLocal() as db:
        if event_type == "sub_event":
            event = db.query(SubEventORM).filter(SubEventORM.id == event_id).first()
        else:
            event = db.query(MainEventORM).filter(MainEventORM.id == event_id).first()

        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")

        if event_type == "sub_event":
            existing = db.query(UserGoingORM).filter(
                UserGoingORM.user_id == current_user.user_id,
                UserGoingORM.sub_event_id == event_id
            ).first()
        else:
            existing = db.query(UserGoingORM).filter(
                UserGoingORM.user_id == current_user.user_id,
                UserGoingORM.main_event_id == event_id
            ).first()

        if existing:
            db.delete(existing)
            event.going_count = max((event.going_count or 0) - 1, 0)
            db.commit()
            db.refresh(event)

        return {"going_count": event.going_count}

# ----- WebSocket endpoint -----
@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    Protocol:
        Client sends: "get_events"
        Server responds with: JSON array of event objects
    """

    # Accept the WebSocket connection
    await websocket.accept()

    # Listen for messages from the client
    try:
        while True: # Infinite loop to keep the connection open
            message = await websocket.receive_text() # Wait for a message from the client

            # Handle "get_events" or "get_main_events" message - returns main events only
            if message in ("get_events", "get_main_events"):
                with SessionLocal() as db:
                    rows = db.query(MainEventORM).all()
                    events_payload = [main_event_orm_to_pydantic(event).model_dump() for event in rows]
                await websocket.send_text(json.dumps(events_payload))
            
            # Handle "get_sub_events" message - returns sub events only
            elif message == "get_sub_events":
                with SessionLocal() as db:
                    rows = db.query(SubEventORM).all()
                    events_payload = [sub_event_orm_to_pydantic(event).model_dump() for event in rows]
                await websocket.send_text(json.dumps(events_payload))
            
            # Handle "get_all_events" message - returns both main and sub events
            elif message == "get_all_events":
                with SessionLocal() as db:
                    main_rows = db.query(MainEventORM).all()
                    sub_rows = db.query(SubEventORM).all()
                    events_payload = (
                        [main_event_orm_to_pydantic(e).model_dump() for e in main_rows] +
                        [sub_event_orm_to_pydantic(e).model_dump() for e in sub_rows]
                    )

                await websocket.send_text(json.dumps(events_payload))

    # Handle WebSocket disconnection
    except WebSocketDisconnect:
        pass # Client disconnected, exit the loop
