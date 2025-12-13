import json
from google import genai

from config import IMAGE_KEYS, IMAGE_KEY_DESCRIPTIONS, LLM_MODEL  # pylint: disable=import-error

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
        "Street": {"type": "STRING", "nullable": True},
        "House_Number": {"type": "STRING", "nullable": True},
        "Zip_Code": {"type": "STRING", "nullable": True},
        "City": {"type": "STRING", "nullable": True},
        "Country": {"type": "STRING", "nullable": True},
        "Room": {"type": "STRING", "nullable": True},
        "Floor": {"type": "STRING", "nullable": True},
        "Speaker": {"type": "STRING", "nullable": True},
        "Organizer": {"type": "STRING", "nullable": True},
        "Registration_Needed": {"type": "BOOLEAN", "nullable": True},
        "URL": {"type": "STRING", "nullable": True},
        "Image_Key": {"type": "STRING", "nullable": True},
        "Event_Type": {"type": "STRING", "nullable": False},  # "main_event" or "sub_event"
        "Main_Event_Temp_Key": {"type": "STRING", "nullable": False},  # Temporary key to link sub_events to main_event
    },
    "required": [
        "Title", "Start_Date", "End_Date", "Start_Time", "End_Time",
        "Description", "Location", "Street", "House_Number", "Zip_Code", 
        "City", "Country", "Room", "Floor", "Speaker", "Organizer", 
        "Registration_Needed", "URL", "Image_Key", "Event_Type", "Main_Event_Temp_Key",
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
    The email text already includes URL content fetched during email download.
    Returns a list of dicts (one per event).
    """
    
    # Generate image key strings for the prompt
    image_keys_str = ", ".join(f'"{k}"' for k in IMAGE_KEYS)
    image_key_descriptions_str = "\n".join(
        f"- {key}: {desc if desc else '(no description provided)'}"
        for key, desc in IMAGE_KEY_DESCRIPTIONS.items()
    )
    
    # System instructions
    system_instruction = f"""

    You are a multilingual assistant that extracts structured event information from university email texts. 
    The emails may be in various languages including English and German. The input text you receive contains
    multiple emails concatenated together.

    The text format is as follows:

    Each email starts with a line like "--------------- EMAIL: X Start ---------------"
    followed by lines with "Subject: ..." and "From: ...", then a blank line, then the email body text.
    
    IMPORTANT: Each email may also include a section "--- URL CONTENT FROM THIS EMAIL ---" which contains
    text content extracted from URLs found in that email. This webpage content provides additional context
    about events mentioned in that specific email.
    
    The email ends with a line like "--------------- EMAIL: X End ---------------".
    
    Some emails describe one event, some describe multiple events, and some are not events at all.
    
    Use the URL content section (when present) to fill in any missing information from the email body,
    such as exact dates, times, locations, speakers, and registration details.
    
    DEFINITION OF AN EVENT

    An event is a scheduled occurrence. It is NOT a invitation to participate in a study, survey, or non-event activity.

    RULES:

    1. Translate any non English text into English, except for names (e.g. building names, street names, institution names)!
    2. Change the time and date formats to match MM/DD/YYYY and HH:MM AM/PM. If unsure, use null. 
    3. When reading emails, pay special attention to lines that indicate event details, for example (in German emails):

        - "Datum:" (date)
        - "Uhrzeit:" (time)
        - "Ort:" (location)

    4. If the email clearly contains a headline, workshop name, lecture title, or event title, USE THAT as the basis for the Title field.
    5. If there is no explicit title, generate a SHORT, CONCISE event title (about 4 to 6 words) that would look good as a calendar headline.
    6. Do NOT use long sentences as titles.
    7. Do NOT include full subtitles with many clauses or questions.
    8. Do NOT summarize the whole email in the title.
    9. When URL content is provided for an email, use it to extract additional details about events.
    10. If the URL content provides more specific information than the email body, prefer the URL content.

    OUTPUT FORMAT

    You must return ONLY a JSON ARRAY ([]) of event objects. Each object in the array must follow this schema:

    - Title (String): The title or name of the event. 
    - Start_Date (String or null): The starting date of the event.
    - End_Date (String or null): The ending date of the event. 
    - Start_Time (String or null): The starting time of the event. If the text contains "c.t." or "s.t.", then interpret "c.t." to start 15 minutes after the hour and "s.t." to start exactly on the hour.
    - End_Time (String or null): If the text contains "c.t." or "s.t.", then interpret "c.t." to end 15 minutes before the hour and "s.t." to end exactly on the hour.
    - Description (String or null): A concise, event-focused description suitable for a calendar entry.  Summarize the purpose, content, and intended audience of the event.  Do NOT describe the email  or administrative availability.
    - Location (String or null): The full location/address of the event as a single string. If the event is remote or online, specify that.
    - Street (String or null): The street name only (without house number).
    - House_Number (String or null): The building/house number.
    - Zip_Code (String or null): The postal/zip code.
    - City (String or null): The city name.
    - Country (String or null): The country name.
    - Room (String or null): The room name or number if specified.
    - Floor (String or null): The floor number if specified.
    - Speaker (String or null): The speaker of the event if available.
    - Organizer (String or null): The organizer of the event if available.
    - Registration_Needed (Boolean or null): Whether registration is needed for the event as true or false.
    - URL (String or null): The URL for more information about the event if available.
    - Image_Key (String or null): Choose one of the following image keys to represent the event: [ {image_keys_str} ]. Here are the image key descriptions that you should use to understand what each image key represents: {image_key_descriptions_str}
    - Event_Type (String, REQUIRED): Must be either "main_event" or "sub_event". Use "main_event" for standalone events or parent events that have sub-events. Use "sub_event" for events that are part of a larger event series (e.g., individual talks in a lecture series, workshops in a conference, sessions in a multi-day event).
    - Main_Event_Temp_Key (String, REQUIRED): A temporary identifier to link related events. For main_events, generate a unique short key (e.g., "conf2024", "lecture_series_ai"). For sub_events, use the SAME key as their parent main_event so they can be linked together. If an event is a standalone main_event with no sub_events, still provide a unique key.

    Do NOT wrap in arrays or extra objects; do NOT add extra keys; do NOT use markdown fences.
    If there is no clear event, don't return anything for this email

    It it possible that one event happens over multiple days; In that case, save the dates and times in a list.
    """

    # User prompt with the email text (URL content is already inline with each email)
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