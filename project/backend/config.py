"""
Centralized configuration for the backend application.
All settings and parameters (except secrets) are defined here.
"""

# ----- Database Configuration -----
DATABASE_URL = "sqlite:///./data/database/tuevent_database.db"


# ----- JWT Authentication Configuration -----
JWT_SECRET_KEY = "RANDOMKEYFORJWTSECRETCHANGEINPRODUCTION"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7
PASSWORD_RESET_EXPIRE_HOURS = 1


# ----- CORS Configuration -----
# Allowed origins for CORS requests (from frontend)
CORS_ORIGINS = [
    # Local
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://193.196.53.179:5173", 

    # Production
    "https://tuevent.de",
    "https://www.tuevent.de",
]


# ----- Scheduler Configuration -----
SCHEDULER_TIMEZONE = "Europe/Berlin"
EMAIL_PIPELINE_CRON_HOURS = "*/6"  # Run every 3 hours
EMAIL_PIPELINE_DEFAULT_LIMIT = 15  # Process up to 15 emails per run


# ----- SMTP Email Configuration -----
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
FRONTEND_URL = "http://localhost:5173"  # Used for password reset links


# ----- Email Downloader Configuration -----
IMAP_HOST = "mailserv.uni-tuebingen.de"
IMAP_PORT = 993
EMAIL_TEMP_DIR = "data/temp_emails"


# ----- LLM Configuration -----
LLM_MODEL = "gemini-2.5-flash"

# Valid image keys for event categorization
IMAGE_KEYS = [
    "daad", "cultural_exchange", "machine_learning", "sports_course", "ai",
    "data_science", "max_plank", "startup", "application_workshop", "debate",
    "museum", "student_organisation", "art_workshop", "erasmus", "networking",
    "sustainability", "blood_donation", "festival_tuebingen", "open_day",
    "theatre", "buddy", "film_screening", "orchestra", "tournament",
    "careerfair", "finance_event", "orientation_week", "training", "city_tour",
    "german_course", "party", "volunteering", "climate", "hike_trip",
    "reading", "workshop", "workshop_png", "colloquium", "info_session",
    "research_fair", "company_talk", "language_course", "science", "science_png",
    "concert_event", "lecture_talk", "consulting_event", "library", "science_fair",
]
