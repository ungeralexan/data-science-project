## Project Structure


← [Back to README](../README.md)

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
            │   ├── EventCalendar.tsx       # Monthly calendar view with clickable events
            │   ├── EventImage.tsx          # Event image display
            │   ├── EventSortButton.tsx     # Sort dropdown control
            │   ├── EventWebsiteButton.tsx  # External website link button
            │   ├── CalendarDownloadButton.tsx  # ICS calendar download
            │   ├── LikeButton.tsx          # Heart icon like/unlike toggle
            │   ├── LikedFilterButton.tsx   # Filter to show liked events only
            │   ├── ViewToggleButton.tsx    # Toggle between list and calendar views
            │   ├── NavBar.tsx              # Navigation bar
            │   ├── ProtectedRoute.tsx      # Auth route wrapper
            │   │
            │   └── css/            # Component stylesheets
            │       ├── App.css
            │       ├── AuthPages.css
            │       ├── EventDetail.css
            │       ├── EventCalendar.css
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