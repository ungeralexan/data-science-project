# tuevent — Tübingen Event Planner

A Data Science project that automatically extracts events from Tübingen university mailing lists and displays them in a modern web application.

**Team:** Veja, Maurice, Alex  
**Tech:** FastAPI · React · SQLite · Google Gemini · JWT

---


## Table of Contents

- [Project Goal](#project-goal)
- [Tech Stack](#tech-stack)
- [Features](#features)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [API Endpoints](#api-endpoints)
- [Running the Project](#running-the-project)
- [Email Pipeline Flow](#email-pipeline-flow)
- [Authentication Flow](#authentication-flow)
- [Development & Contributing](#development--contributing)
- [Testing](#testing)


---

## Project Goal

Turn unstructured university mailing-list messages into a **centralized, personalized event feed**, so students no longer miss:
- Talks & lectures
- Workshops & training sessions
- Career fairs & networking events
- Student group activities
- Department announcements

Events are extracted automatically using LLM-based parsing and displayed in a clean, responsive frontend.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18, TypeScript, Vite, Ant Design |
| **Backend** | FastAPI, Python 3.11+, SQLAlchemy |
| **Database** | SQLite |
| **Authentication** | JWT (JSON Web Tokens) with bcrypt password hashing |
| **Email Processing** | IMAP (university mail server), BeautifulSoup |
| **LLM Integration** | Google Gemini API (event extraction & deduplication) |
| **Scheduling** | APScheduler (automated email processing every 3 hours) |

---

## Features

### Backend
- **Email Ingestion**: Connects to university mail server via IMAP, downloads and parses emails
- **LLM Event Extraction**: Uses Gemini to extract structured event data from unstructured email text
- **Deduplication**: LLM-based comparison to prevent duplicate events in database
- **User Authentication**: Full auth system with registration, login, password reset via email
- **WebSocket API**: Real-time event data delivery to frontend
- **Scheduled Tasks**: Automatic email processing every 3 hours
- **Like System**: API endpoints to like/unlike events with persistent like counts

### Frontend
- **Event Browsing**: Responsive grid layout with event cards
- **Event Sorting**: Sort events by title, date, or time (ascending/descending)
- **Event Filtering**: Filter to show only liked events
- **Like Events**: Heart button to like/unlike events, persisted to localStorage
- **Event Details**: Detailed view with organizer, speaker, registration status, location (with Google Maps link), and description
- **Calendar Download**: Export events as .ics files for calendar apps
- **External Links**: Button to visit event website (with automatic https:// handling)
- **User Accounts**: Registration, login, profile management
- **Password Reset**: Email-based password recovery flow
- **User Interests**: Personalized interest settings for future event recommendations
- **Profile Page**: User info display with recommended events section

---

## Project Structure

```text
data-science-project/
├── docker-compose.yml              # Container orchestration
├── README.md                       # This file
│
└── project/
    ├── backend/
    │   ├── app.py                  # FastAPI application entrypoint
    │   ├── config.py               # Centralized configuration
    │   ├── secrets.json            # API keys & credentials (gitignored)
    │   ├── requirements.txt        # Python dependencies
    │   ├── Dockerfile
    │   │
    │   ├── auth/                   # Authentication module
    │   │   ├── routes.py           # Auth API endpoints (/login, /register, etc.)
    │   │   ├── models.py           # Pydantic models (UserCreate, TokenResponse, etc.)
    │   │   └── utils.py            # JWT handling, password hashing, dependencies
    │   │
    │   ├── services/               # Business logic
    │   │   ├── email_downloader.py # IMAP email fetching
    │   │   ├── email_service.py    # SMTP email sending (password reset)
    │   │   ├── event_pipeline.py   # Full extraction pipeline orchestration
    │   │   ├── event_recognizer.py # LLM-based event extraction
    │   │   └── event_duplicator.py # LLM-based deduplication
    │   │
    │   └── data/
    │       └── database/
    │           └── database_events.py  # SQLAlchemy models & DB setup
    │
    └── frontend/
        ├── index.html
        ├── package.json
        ├── vite.config.ts
        ├── tsconfig.json
        ├── Dockerfile
        │
        └── src/
            ├── App.tsx             # Main app with routing
            ├── main.tsx            # React entrypoint
            │
            ├── pages/              # Page components
            │   ├── Events.tsx      # Event listing page with sort & filter
            │   ├── EventDetail.tsx # Single event view with like, calendar, website link
            │   ├── Login.tsx       # Login page
            │   ├── Register.tsx    # Registration page
            │   ├── Profile.tsx     # User profile with recommended events
            │   ├── Settings.tsx    # User settings & interests
            │   ├── ForgotPassword.tsx
            │   └── ResetPassword.tsx
            │
            ├── components/         # Reusable UI components
            │   ├── EventList.tsx           # Event grid with sorting & filtering
            │   ├── EventImage.tsx          # Event image display
            │   ├── EventSortButton.tsx     # Sort dropdown control
            │   ├── EventWebsiteButton.tsx  # External website link button
            │   ├── CalendarDownloadButton.tsx  # ICS calendar download
            │   ├── LikeButton.tsx          # Heart icon like/unlike toggle
            │   ├── LikedFilterButton.tsx   # Filter to show liked events only
            │   ├── NavBar.tsx              # Navigation bar
            │   ├── ProtectedRoute.tsx      # Auth route wrapper
            │   │
            │   └── css/            # Component stylesheets
            │       ├── App.css
            │       ├── AuthPages.css
            │       ├── EventDetail.css
            │       ├── EventList.css
            │       ├── Events.css
            │       ├── LikeButton.css
            │       ├── NavBar.css
            │       ├── Profile.css
            │       ├── ProtectedRoute.css
            │       └── Settings.css
            │
            ├── context/            # React Context for state management
            │   ├── AuthContext.tsx     # Authentication provider
            │   └── AuthContextType.ts
            │
            ├── hooks/              # Custom React hooks
            │   ├── useAuth.ts      # Auth hook
            │   └── useEvents.ts    # WebSocket events hook
            │
            ├── types/              # TypeScript interfaces
            │   ├── User.ts
            │   └── Event.ts
            │
            └── config/             # Frontend configuration
                └── parameters.json
```

---

## Configuration

### Backend (`config.py`)
All backend settings are centralized in `config.py`:
- Database URL
- JWT settings (secret key, algorithm, expiration)
- CORS allowed origins
- Scheduler settings (timezone, cron schedule)
- SMTP settings (email server, port)
- LLM model selection

### Secrets (`secrets.json`)
Sensitive credentials (not committed to git):
```json
{
    "GEMINI_API_KEY": "...",
    "USER_ZDV": "...",
    "USER_PASSWORD": "...",
    "SMTP_EMAIL": "...",
    "SMTP_PASSWORD": "..."
}
```

---

## API Endpoints

### Authentication (`/api/auth`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Create new user account |
| POST | `/login` | Authenticate and get JWT token |
| GET | `/me` | Get current user info |
| PUT | `/me` | Update user profile |
| DELETE | `/me` | Delete user account |
| POST | `/forgot-password` | Request password reset email |
| POST | `/reset-password` | Reset password with token |

### Events (WebSocket)
| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/events` | Real-time event data stream |

---

## Running the Project

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker (optional)

### Backend
```bash
cd project/backend
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd project/frontend
npm install
npm run dev
```

### Docker
```bash
docker-compose up --build
```

---

## Email Pipeline Flow

```
1. IMAP Connection       → Connect to university mail server
2. Email Download        → Fetch latest emails (configurable limit)
3. HTML Parsing          → Convert HTML emails to plain text
4. Filtering             → Keep only "Rundmail" type emails
5. LLM Extraction        → Gemini extracts structured event data
6. Deduplication         → LLM compares with existing events
7. Database Insert       → Store new events in SQLite
8. WebSocket Broadcast   → Frontend receives updated event list
```

---

## Authentication Flow

```
1. User registers/logs in → Backend creates JWT token
2. Token stored in localStorage → Persists across page reloads
3. Protected requests include → Authorization: Bearer <token>
4. Backend validates token → Extracts user_id, returns data
5. Token expires after 7 days → User must re-login
```

---

## Development & Contributing

This project was developed as part of the *Data Science in Business & Economics* program.

### Branching

- `main` → stable version used for demo / deployment  
- feature branches (e.g. `alex/docs-setup`, `alex/frontend-filters`) for new work

### Code Style

- **Backend**: follow PEP8, type hints where reasonable  
- **Frontend**: TypeScript + React with functional components


## Testing

Basic automated tests (unit and integration) are planned for:

- Backend API endpoints (authentication, events)
- Email pipeline components (parsing, filtering, extraction, deduplication)
- Frontend components (critical pages like Events and Profile)

> **Work in progress:** As of now, only manual end-to-end tests have been performed.  
> See future updates in the `tests/` directory for more details.








