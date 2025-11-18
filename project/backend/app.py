from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import json

app = FastAPI()

# Allow your Vite dev server to talk to the backend
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Data model -----


class Event(BaseModel):
    id: int
    event_title: str
    start_date: str
    end_date: str
    location: Optional[str] = None
    description: Optional[str] = None


FAKE_EVENTS: List[Event] = [
    Event(
        id=1,
        event_title="Data Science Meetup",
        start_date="2025-03-10T18:00:00",
        end_date="2025-03-10T20:00:00",
        location="Campus Building A"
    ),
    Event(
        id=2,
        event_title="Python Workshop",
        start_date="2025-03-12T14:00:00",
        end_date="2025-03-12T16:00:00",
        location="Online",
    ),
]

# ----- WebSocket endpoint -----


@app.websocket("/ws/events")
async def websocket_events(websocket: WebSocket):
    """
    Simple protocol:
      - client connects
      - client sends text "get_events"
      - server responds with JSON list of events
    """
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()

            if message == "get_events":
                # Serialize list[Event] to JSON and send
                events_payload = [e.model_dump() for e in FAKE_EVENTS]
                await websocket.send_text(json.dumps(events_payload))
            # You can add more message types later (e.g., filters)
    except WebSocketDisconnect:
        # client disconnected – just exit the loop
        pass
