import json
from google import genai

# -------- LLM Event Extraction Settings --------

# Schema for a single event object
EVENT_SCHEMA  = {
    "type": "OBJECT",
    "properties": {
        "Title": {"type": "STRING", "nullable": True},
        "Start_Date": {"type": "STRING", "nullable": True},
        "End_Date": {"type": "STRING", "nullable": True},
        "Start_Time": {"type": "STRING", "nullable": True},
        "End_Time": {"type": "STRING", "nullable": True},
        "Description": {"type": "STRING", "nullable": True},
        "Location": {"type": "STRING", "nullable": True},
        "Speaker": {"type": "STRING", "nullable": True},
        "Organizer": {"type": "STRING", "nullable": True},
        "Registration_Needed": {"type": "BOOLEAN", "nullable": True},
        "URL": {"type": "STRING", "nullable": True},
        "Image_Key": {"type": "STRING", "nullable": True},
    },
    "required": [
        "Title", "Start_Date", "End_Date", "Start_Time", "End_Time",
        "Description", "Location", "Speaker", "Organizer", "Registration_Needed", "URL", "Image_Key",
    ],
}

# List of valid image keys
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

# Schema for multiple event objects (array of EVENT_SCHEMA)
SCHEMA_MULTI = {
    "type": "ARRAY",
    "items": EVENT_SCHEMA,
}

image_keys_str = ", ".join(f'"{k}"' for k in IMAGE_KEYS)

#-------- LLM Event Extraction Function --------
def extract_event_info_with_llm(email_text: str) -> dict:
    """
    Uses Gemini to extract multiple events from a text containing multiple emails.
    Returns a list of dicts (one per event).
    """
    
    # System instructions
    system_instruction = f"""

    You are a multilingual assistant that extracts event information from email texts according to a given schema. 
    The emails may be in various languages including English and German. The text you receive contains multiple emails concatenated together.

    The text format is as follows:

    Each email starts with a line like "--------------- EMAIL: X Start ---------------"
    followed by lines with "Subject: ..." and "From: ...", then a blank line, then the email body text,
    and ends with a line like "--------------- EMAIL: X End ---------------".
    
    Only extract if there is a clear event. An event is a scheduled occurrence. It is NOT a invitation to participate in a study, survey, or non-event activity.
    Change the time and date formats to match MM/DD/YYYY and HH:MM AM/PM. If unsure, use null.
    When reading emails, pay special attention to lines starting with:
    - "Datum:" (date)
    - "Uhrzeit:" (time)
    - "Ort:" (location) 
    Return ONLY a single JSON object with exactly these keys and nothing else:

    - Title (String): The title or name of the event. 
    - Start_Date (String or null): The starting date of the event.
    - End_Date (String or null): The ending date of the event. 
    - Start_Time (String or null): The starting time of the event.
    - End_Time (String or null): The ending time of the event.
    - Description (String or null): A description of the event that provides more context and details.
    - Location (String or null): The location of the event. If the event is remote or online, specify that.
    - Speaker (String or null): The speaker of the event if available.
    - Organizer (String or null): The organizer of the event if available.
    - Registration_Needed (Boolean or null): Whether registration is needed for the event as true or false.
    - URL (String or null): The URL for more information about the event if available.
    - Image_Key (String or null): Choose one of the following image keys to represent the event: [ {image_keys_str} ].

    Do NOT wrap in arrays or extra objects; do NOT add extra keys; do NOT use markdown fences.
    If there is no clear event, don't return anything for this email

    It it possible that one event happens over multiple days; In that case, save the dates and times in a list.
    """

    # User prompt with the email text
    user_prompt = f"""

    Extract event information from the following email text:

    {email_text}
    """

    # Combine system instruction and user prompt
    contents = f"{system_instruction}\n\n{user_prompt}"

    # Load Gemini API key from secrets.json
    with open("secrets.json", "r", encoding="utf-8") as f:
        secrets = json.load(f)

    # Create Gemini client
    client = genai.Client(api_key=secrets["GEMINI_API_KEY"])

    # Make the LLM call to generate content with the specified schema
    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config={
            "response_mime_type": "application/json",
            "response_schema": SCHEMA_MULTI,
        },
    )

    # Parse and return the JSON response in the format of a list of dicts (Exp: [{"Title": "...", "Start_Date": "...", ...}, {...}, ...])
    return json.loads(resp.text)