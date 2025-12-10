from typing import Optional
import json
from pydantic import BaseModel

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from data.database.database_events import init_db, SessionLocal, EventORM, UserLikeORM  # pylint: disable=import-error
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
    """
    id: int
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


# ---- Utility functions -----
def orm_to_pydantic(event: EventORM) -> Event:
    """
    Converts an EventORM (SQLAlchemy ORM model) instance to a Pydantic Event model.
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
    scheduler.start()
    print("Scheduler started, email download job scheduled.")

# ----- Shutdown tasks -----
@app.on_event("shutdown")
async def shutdown_event():
    print("Shutting down the backend server...")
    scheduler.shutdown()
    print("Scheduler shut down.")


# ----- Event Like Endpoints -----
@app.post("/api/events/{event_id}/like")
async def like_event(event_id: int, current_user = Depends(get_current_user)):
    """Increment the like count for an event and record the user's like."""

    with SessionLocal() as db:

        event = db.query(EventORM).filter(EventORM.id == event_id).first()

        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Check if user already liked this event
        existing_like = db.query(UserLikeORM).filter(
            UserLikeORM.user_id == current_user.user_id,
            UserLikeORM.event_id == event_id
        ).first()
        
        if existing_like:
            # User already liked this event, return current count
            return {"like_count": event.like_count}
        
        # Create new like record
        new_like = UserLikeORM(user_id=current_user.user_id, event_id=event_id)
        db.add(new_like)
        
        event.like_count = (event.like_count or 0) + 1
        
        db.commit()
        db.refresh(event)
        
        return {"like_count": event.like_count}


@app.post("/api/events/{event_id}/unlike")
async def unlike_event(event_id: int, current_user = Depends(get_current_user)):
    """Decrement the like count for an event and remove the user's like."""
    with SessionLocal() as db:

        event = db.query(EventORM).filter(EventORM.id == event_id).first()

        if event is None:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Find and remove the user's like record
        existing_like = db.query(UserLikeORM).filter(
            UserLikeORM.user_id == current_user.user_id,
            UserLikeORM.event_id == event_id
        ).first()
        
        if existing_like:
            db.delete(existing_like)
            # Ensure like_count doesn't go below 0
            event.like_count = max((event.like_count or 0) - 1, 0)
            db.commit()
            db.refresh(event)
        
        return {"like_count": event.like_count}


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

            # Handle "get_events" message
            if message == "get_events":
                with SessionLocal() as db: # Create a new database session
                    rows = db.query(EventORM).all() # Query all events from the database
                    events_payload = [orm_to_pydantic(event).model_dump() for event in rows] # Convert ORM objects to Pydantic models and then to dicts

                # Send the events data back to the client as JSON
                await websocket.send_text(json.dumps(events_payload))

    # Handle WebSocket disconnection
    except WebSocketDisconnect:
        pass # Client disconnected, exit the loop
