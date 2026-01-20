import json
import re
from google import genai
from google.genai import types

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

# -------- LOG Printing Helper Functions --------

def normalize_thought(text: str) -> str:

    t = text.replace("\r\n", "\n").replace("\r", "\n")     # normalize newlines
    t = t.strip()     # trim leading/trailing whitespace/newlines
    t = re.sub(r"\n\s*\n+", "\n" * 2, t) # Collapses blank lines: \n\s*\n ..
    t = "\n".join(line.rstrip() for line in t.split("\n"))     # Removes trailing spaces per line

    return t

def format_gemini_thought(md: str) -> str:
    """
    Convert Gemini thought summaries like:
      **Title**
      <blank>
      Body...
    into:
      Title: Body...
    with clean spacing.
    """
    t = md.replace("\r\n", "\n").replace("\r", "\n").strip()

    # Split into segments that start with **Title**
    # Captures titles and their following text until next **Title** or end.
    pattern = re.compile(r"\*\*(.+?)\*\*\s*\n+(.*?)(?=\n+\*\*.+?\*\*|\Z)", re.DOTALL)

    parts = []
    for title, body in pattern.findall(t):
        title = title.strip()
        body = body.strip()

        # Collapse whitespace/newlines inside body to single spaces
        body = re.sub(r"\s+", " ", body)

        parts.append(f"{title}: {body}")

    # If nothing matched (unexpected format), just collapse whitespace and return
    if not parts:
        return re.sub(r"\s+", " ", t)

    # Separate formatted sections with a blank line (like your desired output)
    return "\n\n".join(parts)

def indent_block(text: str, prefix: str = "  ") -> str:
    return "\n".join(prefix + line if line else prefix.rstrip() for line in text.split("\n"))

#-------- LLM Event Extraction Function --------
def extract_event_info_with_llm(email_text: str) -> dict:
    """
    Use a Gemini LLM to extract structured event information from the provided email text.
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
    II.11. DO NOT guess or invent missing information.
    II.12. If there are multiple plausible values for a field (especially dates/times), prefer the value that is explicitly labeled as the event date/time. 
    II.13. Treat dates embedded inside URLs (e.g., blog permalinks) as low-confidence unless the surrounding text explicitly labels them as the event date.
    II.14. Date/Time selection heuristic:
    - Prefer date/time values that appear near event marker keywords such as: "am", "on", "Datum", "date", "Uhrzeit", "time", "Beginn", "start", "von", "bis", "Ort", "location", "Treffpunkt".
    - Deprioritize dates that appear near words like: "Deadline", "Anmeldefrist", "Bewerbungsfrist", "apply by", "registration deadline", unless explicitly stated as the event date.
    - If the email and the URL content disagree on the event date/time, prefer the URL content ONLY if it is clearly an event page for the same event and explicitly states the event date/time.
    II.15. Location validity rule:
    If the location text indicates that the location will be announced later (e.g., "will be announced", "to be announced", "upon registration confirmation", "Ort wird bekanntgegeben"), then set Location/Street/House_Number/Zip_Code/City/Country/Room/Floor to "Location TBA".
    II.17. Role disambiguation:
    - Speaker: only assign when the text clearly indicates a person is presenting (e.g., "Vortrag von", "talk by", "speaker", "lecture by", "mit dabei", "keynote"). Do NOT use signature names as Speaker unless explicitly described as presenting.
    - Organizer: the hosting institution/team/department responsible for the event (often from "From:" line, signature block organization, or "organisiert von/hosted by").
    - If a person is only listed as a contact ("Kontakt", "for questions", email signature), do NOT put them in Speaker; keep them out of Speaker and optionally mention them in Description if useful.



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
    - Location (String or null): A short description of where the event takes place. For ONLINE-ONLY events, set this to exactly "Online". For HYBRID events (both physical and online), set this to "Hybrid" or include both (e.g., "Hybrid: Room 123 & Online"). For IN-PERSON events, use the venue/building name (not the full street address).
    - Street (String or null): The street name only (without house number). IMPORTANT: For ONLINE-ONLY events, this MUST be null. Only populate for events with a physical location.
    - House_Number (String or null): The building/house number. IMPORTANT: For ONLINE-ONLY events, this MUST be null.
    - Zip_Code (String or null): The postal/zip code. IMPORTANT: For ONLINE-ONLY events, this MUST be null.
    - City (String or null): The city name. IMPORTANT: For ONLINE-ONLY events, this MUST be null.
    - Country (String or null): The country name. IMPORTANT: For ONLINE-ONLY events, this MUST be null.
    - Room (String or null): The room name or number if specified. IMPORTANT: For ONLINE-ONLY events, this MUST be null.
    - Floor (String or null): The floor number if specified. IMPORTANT: For ONLINE-ONLY events, this MUST be null.
    - Language (String or null): The primary language of the event (e.g., "English", "German", etc.) if specified. If not specified, set to null. Make sure to use language names in English and only insert actual language names and not made up/fake languages, abbreviations or codes. 
    - Speaker (String or null): The speaker (person giving the talk, speech, etc.) of the event if available.
    - Organizer (String or null): The organizer (person organizing the event) if available.
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

    answer_parts = []

    stream = client.models.generate_content_stream(
        model=RECOGNITION_LLM_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SCHEMA_MULTI,
            thinking_config=types.ThinkingConfig(
                include_thoughts=True,
            ),
            #tools=[{"url_context": {}}],
        ),
    )
    
    last_thought = None

    print(RECOGNITION_LLM_MODEL + " starts thinking ...")
    print("")

    for chunk in stream:

        # Some chunks may not contain candidates
        if not getattr(chunk, "candidates", None):
            continue

        # Process each part
        for part in chunk.candidates[0].content.parts:

            # Skip parts with no text
            if not getattr(part, "text", None):
                continue

            # Printing thoughts
            if getattr(part, "thought", False):
                raw = part.text

                # Normalize the thought text
                normalized_thought = format_gemini_thought(raw)

                 # Skip duplicate thoughts and empty thoughts
                if not normalized_thought or normalized_thought == last_thought:
                    continue

                last_thought = normalized_thought

                # Indent and print the thought block
                print(indent_block(normalized_thought, prefix="    "))  # 4-space indent
                print("")

            # Collect answer parts
            else:
                # Actual answer (JSON text) arrives here
                answer_parts.append(part.text)

    # Parse and return the JSON response in the format of a list of dicts (Exp: [{"Title": "...", "Start_Date": "...", ...}, {...}, ...])
    try:
        final_json_str = "".join(answer_parts)

        return json.loads(final_json_str)
    except json.JSONDecodeError as e:
        print("[event_recognizer] Failed to parse LLM JSON:", e)
        return None