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
    image_key: Optional[str] = None


FAKE_EVENTS: List[Event] = [
    Event(
        id=1,
        event_title="Data Science Meetup",
        start_date="2025-03-10T18:00:00",
        end_date="2025-03-10T20:00:00",
        location="Campus Building A",
        description="This is a meetup for data science enthusiasts to discuss the latest trends in the field.",
        image_key="data_science",
    ),
    Event(
        id=2,
        event_title="Python Workshop",
        start_date="2025-03-12T14:00:00",
        end_date="2025-03-12T16:00:00",
        location="Online",
        description="A hands-on workshop to learn Python programming from scratch.",
        image_key="workshop",
    ),
    Event(
        id=3,
        event_title="AI in Healthcare Talk",
        start_date="2025-03-15T17:00:00",
        end_date="2025-03-15T18:30:00",
        location="Campus Building B, Room 204",
        description="Guest speakers present real-world applications of AI and machine learning in modern healthcare.",
        image_key="ai",
    ),
    Event(
        id=4,
        event_title="Startup Pitch Night",
        start_date="2025-03-18T19:00:00",
        end_date="2025-03-18T21:00:00",
        location="Innovation Hub Auditorium",
        description="Student teams pitch their startup ideas to a panel of mentors and potential investors.",
        image_key="startup",
    ),
    Event(
        id=5,
        event_title="Intro to Cloud Computing",
        start_date="2025-03-20T16:00:00",
        end_date="2025-03-20T17:30:00",
        location="Online",
        description="An introductory session on cloud platforms, deployment models, and core services.",
        image_key="science",
    ),
    Event(
        id=6,
        event_title="Career Fair Preparation Session",
        start_date="2025-03-22T13:00:00",
        end_date="2025-03-22T14:30:00",
        location="Career Center, Room 101",
        description="Learn how to optimize your CV, LinkedIn, and elevator pitch before the upcoming career fair.",
        image_key="careerfair",
    ),
    Event(
        id=7,
        event_title="Networking Evening for Tech Students",
        start_date="2025-03-24T18:30:00",
        end_date="2025-03-24T20:30:00",
        location="Campus Cafeteria",
        description="An informal networking event to connect with fellow students, alumni, and industry partners.",
        image_key="networking",
    ),
    Event(
        id=8,
        event_title="Machine Learning Study Group",
        start_date="2025-03-26T17:00:00",
        end_date="2025-03-26T19:00:00",
        location="Library Study Room C",
        description="Weekly study group to review ML concepts, solve exercises, and discuss research papers.",
        image_key="machine_learning",
    ),
    Event(
        id=9,
        event_title="Hackathon Kickoff",
        start_date="2025-03-28T09:00:00",
        end_date="2025-03-28T10:00:00",
        location="Innovation Hub Lobby",
        description="Opening session for the 24-hour campus hackathon, including team formation and rules overview.",
        image_key="startup",
    ),
    Event(
        id=10,
        event_title="End-of-Semester Social",
        start_date="2025-03-30T19:00:00",
        end_date="2025-03-30T22:00:00",
        location="Student Lounge",
        description="Casual social gathering with music, snacks, and drinks to celebrate the end of the semester.",
        image_key="party",
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
