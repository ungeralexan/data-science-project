import json
from google import genai

from config import IMAGE_KEYS, IMAGE_KEY_DESCRIPTIONS, RECOGNITION_LLM_MODEL  # pylint: disable=import-error

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
        "Language": {"type": "STRING", "nullable": True},
        "Speaker": {"type": "STRING", "nullable": True},
        "Organizer": {"type": "STRING", "nullable": True},
        "Registration_Needed": {"type": "BOOLEAN", "nullable": True},
        "URL": {"type": "STRING", "nullable": True},
        "Registration_URL": {"type": "STRING", "nullable": True},
        "Meeting_URL": {"type": "STRING", "nullable": True},
        "Image_Key": {"type": "STRING", "nullable": True},
        "Event_Type": {"type": "STRING", "nullable": False},  # "main_event" or "sub_event"
        "Main_Event_Temp_Key": {"type": "STRING", "nullable": False},  # Temporary key to link sub_events to main_event
    },
    "required": [
        "Title", "Start_Date", "End_Date", "Start_Time", "End_Time",
        "Description", "Location", "Street", "House_Number", "Zip_Code", 
        "City", "Country", "Room", "Floor", "Language", "Speaker", "Organizer", 
        "Registration_Needed", "URL", "Registration_URL", "Meeting_URL", 
        "Image_Key", "Event_Type", "Main_Event_Temp_Key",
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
    The emails may be in various languages including English and German. One email might also include multiple languages. 
    The input text you receive contains multiple emails concatenated together.

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
    
    I) DEFINITION OF AN EVENT:

    I.1) An event is a scheduled occurrence. It is NOT a invitation to participate in a study, survey, or non-event activity.
    I.2) There are main events and sub events. Main events are the primary events, while sub events are part of a larger event series. (e.g., 
    individual talks in a lecture series, workshops in a conference, sessions in a multi-day event).
    I.3) There cannot be a sub event without a main event!
    I.4) If an email mentions multiple weekdays for an event without specific dates, this might indicate a recurring event. In that case, treat each day as a single main event or sub event if part of a main event (e.g., a weekly seminar) and add the weekday in the event title.

    II) General RULES:

    II.1. Translate any non English text into English, except for names (e.g. building names, street names, institution names)!
    II.2. Change the time and date formats to match MM/DD/YYYY and HH:MM AM/PM. If unsure, use null. 
    II.3. When reading emails, pay special attention to lines that indicate event details, for example (in German emails):

        - "Datum:" (date)
        - "Uhrzeit:" (time)
        - "Ort:" (location)
        - "Anmeldung" (registration)

    II.4. If the email clearly contains a headline, workshop name, lecture title, or event title, USE THAT as the basis for the Title field.
    II.5. If there is no explicit title, generate a SHORT, CONCISE event title (about 4 to 6 words) that would look good as a calendar headline.
    II.6. Do NOT use long sentences as titles.
    II.7. Do NOT include full subtitles with many clauses or questions.
    II.8. Do NOT summarize the whole email in the title.
    II.9. When URL content is provided for an email, use it to extract additional details about events.
    II.10. If the URL content provides more specific information than the email body, prefer the URL content.
    
    III) DESCRIPTION QUALITY RULES:

    The Description must be written as if it will be shown in a calendar entry to an end user.

    III.1 Describe what will happen, not how the email is presented. (No mention of the email itself.)
    III.2 Write in neutral, informative language that is clear and concise.
    III.3 Focus on the event content: who will be involved, what will happen, and why it's important.

    A good Description answers:
    - What is happening?
    - Who is it for?
    - What will participants gain or experience?

    IV) URL and REGISTRATION QUALITY RULES:

    IV.1 There are three types of URLs you may find in the email text:
        - General information URLs about the event (put these in the "URL" field)
        - Registration URLs where users can sign up for the event (put these in the "Registration_URL" field)
        - Online meeting URLs for virtual attendance (put these in the "Meeting_URL" field)
    IV.2 If the email or URL content explicitly mentions that registration is required, set "Registration_Needed" to true.
    IV.3 If a Registration_URL is provided, this automatically means that registration is required regardless of what the email says and the field Registration_Needed should be set to true.
    IV.4 There can never the case that Registration_Needed is false but there is a Registration_URL.
    IV.5 If there is no clear indication about registration requirements and also no Registration_URL provided, set "Registration_Needed" to null.
    IV.6 Do NOT put registration links or online meeting links in the general "URL" field. This means that the url in the field "URL" cannot be the same as in "Registration_URL" or "Meeting_URL".
    IV.7 If the event is online or hybrid and there is a link to join the virtual meeting (e.g., Zoom, Microsoft Teams, WebEx, Google Meet links, etc.), put that URL in the "Meeting_URL" field.
    IV.8 The field registration_url and meeting_url cannot contain the same URL.
    IV.9 If there is no URL for a field, set it to null.
    
    IV) OUTPUT FORMAT:

    IV.1. You must return ONLY a JSON ARRAY ([]) of event objects. Each object in the array must follow this schema:

    - Title (String): The title or name of the event. 
    - Start_Date (String or null): The starting date of the event. There can only be one start date!
    - End_Date (String or null): The ending date of the event. There can only be one end date!
    - Start_Time (String or null): The start time of the event. There can only be one start time! If the text contains "c.t." or "s.t.", then interpret "c.t." to start 15 minutes after the hour and "s.t." to start exactly on the hour.
    - End_Time (String or null): The end time of the event. There can only be one end time! If the text contains "c.t." or "s.t.", then interpret "c.t." to end 15 minutes before the hour and "s.t." to end exactly on the hour.
    - Description (String or null): A concise, event-focused description suitable for a calendar entry.  Summarize the purpose, content, and intended audience of the event.  Do NOT describe the email  or administrative availability.
    - Location (String or null): The full location/address of the event as a single string. If the event is remote or online, specify that.
    - Street (String or null): The street name only (without house number).
    - House_Number (String or null): The building/house number.
    - Zip_Code (String or null): The postal/zip code.
    - City (String or null): The city name.
    - Country (String or null): The country name.
    - Room (String or null): The room name or number if specified.
    - Floor (String or null): The floor number if specified.
    - Language (String or null): The primary language of the event (e.g., "English", "German", etc.) if specified. If not specified, set to null. Make sure to use language names in English and only insert actual language names and not made up/fake languages, abbreviations or codes. 
    - Speaker (String or null): The speaker of the event if available.
    - Organizer (String or null): The organizer of the event if available.
    - Registration_Needed (Boolean or null): Whether registration is needed for the event as true or false.
    - URL (String or null): A URL for general information about the event if available. 
    - Registration_URL (String or null): A URL where users can register for the event if available.
    - Meeting_URL (String or null): A URL for online meetings (Zoom, Teams, etc.) if available.
    - Image_Key (String or null): Choose one of the following image keys to represent the event: [ {image_keys_str} ]. Here are the image key descriptions that you should use to understand what each image key represents: {image_key_descriptions_str}
    - Event_Type (String, REQUIRED): Must be either "main_event" or "sub_event". Use "main_event" for standalone events or parent events that have sub-events. Use "sub_event" for events that are part of a larger event series (e.g., individual talks in a lecture series, workshops in a conference, sessions in a multi-day event). 
    - Main_Event_Temp_Key (String, REQUIRED): A temporary identifier to link related events. For main_events, generate a unique short key (e.g., "conf2024", "lecture_series_ai"). For sub_events, use the SAME key as their parent main_event so they can be linked together. If an event is a standalone main_event with no sub_events, still provide a unique key. Sub events must have a corresponding main event with the same Main_Event_Temp_Key.

    IV.2. Do NOT wrap in arrays or extra objects.
    IV.3. Do NOT add extra keys.
    IV.4. Do NOT use markdown fences. 
    IV.5. If there is no clear event, don't return anything for this email
    IV.6. Do NOT wrap any characters (such as German umlauts ä, ö, ü) in angle brackets like <ä> or <ü>.
    IV.7. Do NOT use XML-like or HTML-like tags in your output.
    IV.8. It it possible that one event happens over multiple days; In that case, save the dates and times in a list.
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
        model=RECOGNITION_LLM_MODEL,
        contents=contents,
        config={
            "response_mime_type": "application/json",
            "response_schema": SCHEMA_MULTI,
        },
    )

    # Parse and return the JSON response in the format of a list of dicts (Exp: [{"Title": "...", "Start_Date": "...", ...}, {...}, ...])
    try:
        parts = resp.candidates[0].content.parts
        text = "".join(getattr(part, "text", "") for part in parts)

        return json.loads(text)
    except json.JSONDecodeError as e:
        print("[event_recognizer] Failed to parse LLM JSON:", e)
        return None