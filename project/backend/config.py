"""
Centralized configuration for the backend application.
All settings and parameters (except secrets) are defined here.
"""
# ----- General Configuration -----

DEFAULT_THEME = "light"

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
RECOGNITION_LLM_MODEL = "gemini-3-flash-preview" #"gemini-2.5-flash"
#RECOMMENDATION_LLM_MODEL = "google/gemini-2.0-flash-exp:free"
RECOMMENDATION_LLM_MODEL = "gpt-oss-120b:free"

# Image keys for event categorization, with optional descriptions (can be empty).
IMAGE_KEY_DESCRIPTIONS = {
    "ai": "Events centered on artificial intelligence, innovation, or tech developments.",
    "art_workshop": "Workshops involving creative activities like painting, drawing, or crafting.",
    "blood_donation": "Blood donation drives or health-related volunteer events.",
    "buddy": "Buddy program meetups that connect international and local students.",
    "careerfair": "Career fairs, company recruiting events, or job market expos.",
    "city_tour": "Guided city tours, sightseeing events, or local exploration activities.",
    "climate": "Events focused on climate change, environmental protection, or sustainability discussions.",
    "colloquium": "Academic colloquia, research talks, or scholarly presentations.",
    "company_talk": "Talks or presentations by companies about careers, projects, or industry insights.",
    "concert_event": "Concerts, live music performances, or musical gatherings.",
    "consulting_event": "Consulting-related events, workshops, or company sessions.",
    "cultural_exchange": "Events focused on international meetups, cultural sharing, or global community activities.",
    "data_science": "Data science lectures, workshops, or analytics-related academic events.",
    "daad": "Events related to DAAD programs, scholarships, or studying abroad.",
    "debate": "Academic debates, discussion rounds, or argumentation-focused events.",
    "erasmus": "Events related to Erasmus exchanges, international mobility, or study-abroad programs.",
    "festival": "General festival that is not related to Tuebingen.",
    "festival_tuebingen": "Local Tuebingen festivals, city celebrations, or public cultural events.",
    "film_screening": "Movie nights, film screenings, or cinema-related events.",
    "finance_event": "Events related to finance, investing, economics, or industry talks.",
    "german_course": "German language classes, language cafés, or linguistic workshops.",
    "graduation": "Events related to university graduation and finishing studies.",
    "hike_trip": "Hiking trips, outdoor excursions, or nature exploration events.",
    "info_session": "Informational sessions explaining programs, opportunities, or administrative topics.",
    "language_course": "Language learning courses or language-focused workshops.",
    "lecture_talk": "Lectures, talks, or keynote presentations by experts or professors.",
    "library": "Library-related events, study sessions, or academic resource introductions.",
    "machine_learning": "Events about machine learning topics, courses, research talks, or tech workshops.",
    "max_plank": "Events hosted by or connected to the Max Planck Institute.",
    "museum": "Museum visits, guided tours, or cultural exhibitions.",
    "networking": "Networking events where participants meet, connect, and exchange professional contacts.",
    "open_day": "University open days, campus tours, or informational orientation events.",
    "orchestra": "Orchestra concerts, classical music events, or ensemble performances.",
    "orientation_week": "Welcome week activities for new students, including social and informational events.",
    "party": "Social parties, student celebrations, or nightlife events.",
    "resume_workshop": "Workshops about job applications, CVs, cover letters, or career preparation.",
    "reading": "Reading circles, book clubs, or literature-related events.",
    "research_fair": "Research fairs showcasing broad research projects, posters, or student research.",
    "science": "Science-related events, STEM activities, or academic presentations.",
    "science_fair": "Science fairs showcasing specific scientific projects and discoveries.",
    "sports_course": "University sports classes, training sessions, or athletic activities.",
    "startup": "Entrepreneurship events, startup talks, or innovation meetups.",
    "student_organization": "Events organized by student clubs, associations, or campus groups.",
    "sustainability": "Events focused on environmental sustainability, climate action, or ecological awareness.",
    "theatre": "Theatre performances, drama workshops, or stage arts events.",
    "tournament": "Sports tournaments, competitions, or competitive game events.",
    "training": "Skill-building training sessions, workshops, or certification activities.",
    "volunteering": "Volunteer activities, community service, or social impact events.",
    "workshop": "General workshops focused on learning a specific skill or topic.",
}

# Preserved flat list for callers that only need the keys.
IMAGE_KEYS = list(IMAGE_KEY_DESCRIPTIONS.keys())
