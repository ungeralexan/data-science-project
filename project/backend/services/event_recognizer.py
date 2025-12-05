import json
from google import genai

from config import IMAGE_KEYS, LLM_MODEL  # pylint: disable=import-error

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

# Schema for multiple event objects (array of EVENT_SCHEMA)
SCHEMA_MULTI = {
    "type": "ARRAY",
    "items": EVENT_SCHEMA,
}

#-------- LLM Event Extraction Function --------
def extract_event_info_with_llm(email_text: str) -> dict:
    """
    Uses Gemini to extract multiple events from a text containing multiple emails.
    Returns a list of dicts (one per event).
    """
    
    # Generate image keys string for the prompt
    image_keys_str = ", ".join(f'"{k}"' for k in IMAGE_KEYS)
    
    # System instructions
    system_instruction = f"""

    You are a multilingual assistant that extracts structured event information from university email texts. 
    The emails may be in various languages including English and German. The input text you receive contains
    multiple emails concatenated together.

    The text format is as follows:

    Each email starts with a line like "--------------- EMAIL: X Start ---------------"
    followed by lines with "Subject: ..." and "From: ...", then a blank line, then the email body text,
    and ends with a line like "--------------- EMAIL: X End ---------------".
    
    Some emails describe one event, some describe multiple events, and some are not events at all.
    
    DEFINITION OF AN EVENT

    An event is a scheduled occurrence. It is NOT a invitation to participate in a study, survey, or non-event activity.

    LANGUAGE OF OUTPUT

    Regardless of the original email language, return all textual fields in English,
    except for proper names (e.g. building names, street names, institution names),
    which you may keep as in the original.

    DATE AND TIME HANDLING

    Change the time and date formats to match MM/DD/YYYY and HH:MM AM/PM. If unsure, use null.
    When reading emails, pay special attention to lines that indicate event details, for example (in German emails):

    - "Datum:" (date)
    - "Uhrzeit:" (time)
    - "Ort:" (location)

    TITLE RULES

    - If the email clearly contains a headline, workshop name, lecture title, or event title, USE THAT as the basis for the Title field (translated to English if needed, but keep names).
    - If there is no explicit title, generate a SHORT, CONCISE event title (about 5–10 words)  that would look good as a calendar headline.
    - Do NOT use long sentences as titles.
    - Do NOT include full subtitles with many clauses or questions.
    - Do NOT summarize the whole email in the title.

    OUTPUT FORMAT

    You must return ONLY a JSON ARRAY ([]) of event objects. Each object in the array must follow this schema:

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
        model=LLM_MODEL,
        contents=contents,
        config={
            "response_mime_type": "application/json",
            "response_schema": SCHEMA_MULTI,
        },
    )

    # Parse and return the JSON response in the format of a list of dicts (Exp: [{"Title": "...", "Start_Date": "...", ...}, {...}, ...])
    return json.loads(resp.text)