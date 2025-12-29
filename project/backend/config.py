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
EMAIL_PIPELINE_CRON_HOURS = "*/6"  # Run every 6 hours
EMAIL_PIPELINE_DEFAULT_LIMIT = 30  # Process up to 30 emails per run


# ----- SMTP Email Configuration -----
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
FRONTEND_URL = "http://localhost:5173"  # Used for password reset links


# ----- Email Downloader Configuration -----
IMAP_HOST = "mailserv.uni-tuebingen.de"
IMAP_PORT = 993
EMAIL_TEMP_DIR = "data/temp_emails"

# ----- LLM Configuration -----
#RECOGNITION_LLM_MODEL = "gemini-3-flash-preview" #Model used for event recognition and extraction
RECOGNITION_LLM_MODEL = "gemini-2.5-flash" #Model used for event recognition and extraction
DUPLICATION_LLM_MODEL = "gemini-2.5-flash" #Model used for event duplication detection
RECOMMENDATION_LLM_MODEL = "gpt-oss-120b:free"

# Image keys for event categorization, with optional descriptions (can be empty).
IMAGE_KEY_DESCRIPTIONS = {
    # --- Tech / Data (topic) ---
    "ai": (
        "Use for: applied AI and GenAI, AI products, AI innovation/strategy, AI ethics/policy (non-technical). "
        "Do not use for: deep ML methods, model training, architectures, algorithm details. "
        "If overlapping: prefer ai when the focus is applications/impact rather than methods; otherwise use machine_learning."
    ),
    "data_science": (
        "Use for: data analytics and data workflows (EDA, statistics, visualization, dashboards, Python/R analytics, basic data pipelines). "
        "Do not use for: ML/DL model training and algorithm-focused sessions (use machine_learning). "
        "If overlapping: prefer data_science when analysis/insights are central and predictive modeling is not the main topic."
    ),
    "machine_learning": (
        "Use for: technical ML/DL methods (model training, architectures, algorithms, evaluation, research papers, ML coding). "
        "Do not use for: general AI innovation/product talks (use ai). "
        "If overlapping: prefer machine_learning when predictive modeling and methods are central; otherwise use data_science or ai."
    ),

    # --- Environment (topic) ---
    "climate": (
        "Use for: climate change specifically (emissions, mitigation/adaptation, climate science, climate policy). "
        "Do not use for: general sustainability, ESG, circular economy without climate-change framing (use sustainability). "
        "If overlapping: prefer climate when climate change is explicitly named or clearly the primary framing."
    ),
    "sustainability": (
        "Use for: sustainability broadly (ESG, circular economy, resources, sustainable living, campus sustainability initiatives). "
        "Do not use for: climate-science/policy events primarily about climate change (use climate). "
        "If overlapping: prefer sustainability when the framing is general sustainability without a clear climate-change focus."
    ),

    # --- Academic / Education (format) ---
    "colloquium": (
        "Use for: formal academic research colloquia/seminars (typically department/institute research presentations with Q&A). "
        "Do not use for: general public lectures not framed as a research seminar (use lecture_talk). "
        "If overlapping: prefer colloquium when it is clearly a research-seminar format or a recurring colloquium series."
    ),
    "debate": (
        "Use for: structured debates or argumentation formats (pro/contra, moderated debate, discussion round as the main format). "
        "Do not use for: standard lectures with Q&A (use lecture_talk or colloquium). "
        "If overlapping: prefer debate when the event is explicitly advertised as a debate/discussion round."
    ),
    "info_session": (
        "Use for: informational sessions explaining programs, opportunities, rules, processes, or administration. "
        "Do not use for: hands-on skill learning (use workshop or training); talks by experts without administrative/program focus (use lecture_talk). "
        "If overlapping: prefer info_session when the primary goal is explanation of a program/process."
    ),
    "lecture_talk": (
        "Use for: lectures, talks, keynotes, guest speaker presentations (mostly listening, not hands-on). "
        "Do not use for: formal research seminars (use colloquium); hands-on sessions (use workshop). "
        "If overlapping: prefer lecture_talk when the format is primarily a presentation rather than an interactive activity."
    ),
    "library": (
        "Use for: library-organized events (library introductions, research resources, study events hosted by the library). "
        "Do not use for: generic study sessions not tied to the library. "
        "If overlapping: prefer library when the organizer/venue and topic are clearly library-related."
    ),
    "open_day": (
        "Use for: university open days and campus visits aimed at prospective students/visitors (campus tours + program info). "
        "Do not use for: welcome-week onboarding for new enrolled students (use orientation_week). "
        "If overlapping: prefer open_day when the target audience is prospective students or the public."
    ),
    "orientation_week": (
        "Use for: welcome/orientation week events for new students (onboarding series, welcome program). "
        "Do not use for: open days aimed at prospective students (use open_day). "
        "If overlapping: prefer orientation_week when it is explicitly part of a welcome/orientation week."
    ),
    "research_fair": (
        "Use for: research fairs/showcases with multiple projects, posters, booths, or presentations in parallel. "
        "Do not use for: competition-style science fairs or demo fairs framed as a science fair (use science_fair). "
        "If overlapping: prefer research_fair when the format is a multi-project poster/booth showcase."
    ),
    "science": (
        "Use for: general STEM/science-themed events not better matched by colloquium, research_fair, or science_fair. "
        "Do not use for: formal research seminars (use colloquium) or fair/showcase formats (use research_fair or science_fair). "
        "If overlapping: use science only when no more specific science-related key fits."
    ),
    "science_fair": (
        "Use for: science fairs with demos/exhibits and ‘fair’ framing (often student projects, sometimes competition). "
        "Do not use for: professional poster sessions or research showcases (use research_fair). "
        "If overlapping: prefer science_fair when the event is explicitly called a science fair."
    ),

    # --- Career / Business (topic or format) ---
    "careerfair": (
        "Use for: career fairs and recruiting expos with multiple employers/booths. "
        "Do not use for: a single-company session or presentation (use company_talk). "
        "If overlapping: prefer careerfair when there are many employers present and recruiting is the main purpose."
    ),
    "company_talk": (
        "Use for: talks or presentations by a single company about careers, projects, or industry insights. "
        "Do not use for: multi-company recruiting fairs (use careerfair). "
        "If overlapping: prefer company_talk when one employer/company is the main focus."
    ),
    "consulting_event": (
        "Use for: consulting-focused events (consulting firms, case workshops, consulting career sessions). "
        "Do not use for: general professional mixers without consulting focus (use networking). "
        "If overlapping: prefer consulting_event when consulting is explicitly the theme or organizer domain."
    ),
    "finance_event": (
        "Use for: finance/economics/investing/fintech topics (markets, banking, investing, economic policy). "
        "Do not use for: recruiting fairs (use careerfair) or generic networking mixers (use networking). "
        "If overlapping: prefer finance_event when finance/economics content is the primary topic."
    ),
    "networking": (
        "Use for: networking mixers/meetups where making contacts is the explicit goal. "
        "Do not use for: parties/nightlife (use party) or talks where listening is the primary activity (use lecture_talk or company_talk). "
        "If overlapping: prefer networking when professional connection-building is explicitly advertised."
    ),
    "resume_workshop": (
        "Use for: job application preparation (CV, cover letter, interview training, LinkedIn, application strategy). "
        "Do not use for: recruiting expos (use careerfair) or general skills workshops unrelated to applications (use workshop). "
        "If overlapping: prefer resume_workshop whenever the content is explicitly about applications/interviews."
    ),
    "startup": (
        "Use for: entrepreneurship/startup events (founding, pitching, incubators, venture capital, startup ecosystem). "
        "Do not use for: general tech topics without entrepreneurship angle (use ai, machine_learning, or data_science). "
        "If overlapping: prefer startup when entrepreneurship/founding is the primary framing."
    ),

    # --- Mobility / International programs (program/organizer) ---
    "daad": (
        "Use for: DAAD-related events (DAAD scholarships, DAAD programs, DAAD advising). "
        "Do not use for: general exchange without DAAD branding (use erasmus or info_session). "
        "If overlapping: prefer daad when DAAD is explicitly named as organizer or topic."
    ),
    "erasmus": (
        "Use for: Erasmus exchange and mobility events (Erasmus advising, Erasmus student activities tied to Erasmus). "
        "Do not use for: DAAD-branded events (use daad). "
        "If overlapping: prefer erasmus when Erasmus is explicitly named as program/organizer."
    ),

    # --- Language learning (topic/format) ---
    "german_course": (
        "Use for: German language learning (German classes, German language cafés, German practice sessions). "
        "Do not use for: other languages (use language_course). "
        "If overlapping: prefer german_course whenever German is the target language."
    ),
    "language_course": (
        "Use for: language learning courses not specific to German (e.g., English, French, Spanish). "
        "Do not use for: German language learning (use german_course). "
        "If overlapping: prefer language_course when it is clearly a language class/practice format."
    ),

    # --- Student life / Community (context or organizer) ---
    "buddy": (
        "Use for: buddy/tandem programs connecting international and local students (buddy framing). "
        "Do not use for: general cultural meetups without buddy framing (use cultural_exchange). "
        "If overlapping: prefer buddy when a buddy/tandem program is explicitly named."
    ),
    "cultural_exchange": (
        "Use for: international/cultural exchange meetups (intercultural evenings, international community events). "
        "Do not use for: buddy-program specific events (use buddy). "
        "If overlapping: prefer cultural_exchange when intercultural exchange is the explicit theme."
    ),
    "student_organization": (
        "Use for: events organized by student clubs/associations (club-branded organizer). "
        "Do not use for: official program/administration sessions (use info_session) or buddy-program events (use buddy). "
        "If overlapping: prefer student_organization when a student club is clearly the organizer."
    ),

    # --- Volunteering / Health (type) ---
    "blood_donation": (
        "Use for: blood donation drives and blood donation appointment events. "
        "Do not use for: general volunteering not centered on blood donation (use volunteering). "
        "If overlapping: prefer blood_donation whenever donating blood is the explicit activity."
    ),
    "volunteering": (
        "Use for: volunteer/community service/social impact activities (active helping). "
        "Do not use for: blood donation events (use blood_donation). "
        "If overlapping: prefer volunteering when the main action is community service rather than attending a talk."
    ),

    # --- Outdoors / Tourism (type) ---
    "city_tour": (
        "Use for: guided city tours, sightseeing, local exploration in an urban setting. "
        "Do not use for: museum-focused visits (use museum) or hiking in nature (use hike_trip). "
        "If overlapping: prefer city_tour when guided sightseeing is the main activity."
    ),
    "hike_trip": (
        "Use for: hiking and outdoor nature excursions (trails, nature exploration, day trips in nature). "
        "Do not use for: city sightseeing tours (use city_tour) or sports classes (use sports_course). "
        "If overlapping: prefer hike_trip when nature/outdoor trekking is central."
    ),
    "museum": (
        "Use for: museum visits, exhibitions, guided museum tours (museum venue is central). "
        "Do not use for: theatre performances (use theatre). "
        "If overlapping: prefer museum when the main activity is visiting an exhibition or museum collection."
    ),

    # --- Arts / Entertainment (format) ---
    "concert_event": (
        "Use for: live music concerts/gigs (bands, artists, live music events not explicitly orchestral). "
        "Do not use for: orchestra/classical ensemble concerts (use orchestra). "
        "If overlapping: prefer concert_event when the event is advertised as a concert but not an orchestra performance."
    ),
    "film_screening": (
        "Use for: film screenings, movie nights, cinema events. "
        "Do not use for: theatre live performances (use theatre). "
        "If overlapping: prefer film_screening whenever a film is being shown."
    ),
    "orchestra": (
        "Use for: orchestra/classical ensemble performances (symphony, chamber orchestra, classical concert). "
        "Do not use for: general live music gigs (use concert_event). "
        "If overlapping: prefer orchestra when the event is explicitly classical/orchestral."
    ),
    "party": (
        "Use for: social parties/nightlife events (celebration, DJ party, club night). "
        "Do not use for: professional networking mixers (use networking). "
        "If overlapping: prefer party when entertainment/socializing is the main purpose."
    ),
    "reading": (
        "Use for: reading circles, book clubs, literature readings, author readings. "
        "Do not use for: general lectures about literature without a reading/club format (use lecture_talk). "
        "If overlapping: prefer reading when books/reading/discussion of literature is central."
    ),
    "theatre": (
        "Use for: theatre performances and stage drama (live performance), and theatre-specific drama workshops. "
        "Do not use for: film screenings (use film_screening). "
        "If overlapping: prefer theatre when it is a live stage performance."
    ),

    # --- Sports (type) ---
    "sports_course": (
        "Use for: sports classes and training sessions (recurring practice, course-style sports sessions). "
        "Do not use for: competitions/tournaments (use tournament). "
        "If overlapping: prefer sports_course when it is a class/training rather than a competitive event."
    ),
    "tournament": (
        "Use for: sports tournaments and competitions (matches, brackets, winners/results). "
        "Do not use for: regular practice sessions (use sports_course). "
        "If overlapping: prefer tournament when competition and results are the focus."
    ),

    # --- Skills / Workshops (format) ---
    "art_workshop": (
        "Use for: creative workshops such as painting, drawing, crafts, DIY, pottery. "
        "Do not use for: general skill workshops not focused on art/crafts (use workshop). "
        "If overlapping: prefer art_workshop when the activity is primarily artistic/craft-based."
    ),
    "training": (
        "Use for: structured training sessions, courses, or certification-oriented learning (curriculum-based). "
        "Do not use for: short one-off hands-on workshops (use workshop). "
        "If overlapping: prefer training when a course structure, certification, or multi-step syllabus is emphasized."
    ),
    "workshop": (
        "Use for: hands-on interactive workshops (learning by doing) not covered by a more specific workshop key. "
        "Do not use for: art/crafts (use art_workshop) or CV/interview content (use resume_workshop) or certification courses (use training). "
        "If overlapping: prefer workshop when active participation is central and no more specific workshop key fits."
    ),

    # --- Institutions / Organizers (organizer) ---
    "max_plank": (
        "Use for: events hosted by or explicitly connected to the Max Planck Institute (MPI). "
        "Do not use for: general science talks without MPI connection (use colloquium or science). "
        "If overlapping: prefer max_plank when MPI branding/hosting is explicitly stated."
    ),

    # --- Milestones (type) ---
    "graduation": (
        "Use for: graduation ceremonies, commencements, official degree-completion events. "
        "Do not use for: generic celebration parties without an official graduation framing (use party). "
        "If overlapping: prefer graduation when the graduation milestone is the explicit core of the event."
    ),

    # --- Festivals (location-scoped type) ---
    "festival": (
        "Use for: festivals that are not clearly Tübingen-based (external/general festivals). "
        "Do not use for: festivals explicitly in Tübingen or branded as Tübingen city/university festivals (use festival_tuebingen). "
        "If overlapping: prefer festival only when it is outside Tübingen or not locally branded."
    ),
    "festival_tuebingen": (
        "Use for: festivals explicitly in Tübingen or branded as Tübingen city/university festivals. "
        "Do not use for: festivals elsewhere (use festival). "
        "If overlapping: prefer festival_tuebingen when the location/branding is clearly Tübingen."
    ),
}



# Preserved flat list for callers that only need the keys.
IMAGE_KEYS = list(IMAGE_KEY_DESCRIPTIONS.keys())
