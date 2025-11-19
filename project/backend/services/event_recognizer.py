import json
from pathlib import Path
import pandas as pd
from typing import List
from google import genai

# -------- JSON schema: multiple events --------
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
    },
    "required": [
        "Title", "Start_Date", "End_Date", "Start_Time", "End_Time",
        "Description", "Location", "Speaker", "Organizer", "Registration_Needed", "URL"
    ],
}

# The top-level schema is an ARRAY of those objects
SCHEMA_MULTI = {
    "type": "ARRAY",
    "items": EVENT_SCHEMA,
}


def extract_event_info_with_llm(email_text: str) -> dict:
    """
    Uses Gemini to extract multiple events from a text containing multiple emails.
    Returns a list of dicts (one per event).
    """

    system_instruction = """

    You are a multilingual assistant that extracts event information from email texts according to a given schema. 
    The emails may be in various languages including English and German. The text you receive contains multiple emails concatenated together.

    The text format is as follows:

    Each email starts with a line like "--------------- EMAIL: X Start ---------------"
    followed by lines with "Subject: ..." and "From: ...", then a blank line, then the email body text,
    and ends with a line like "--------------- EMAIL: X End ---------------".
    
    Only extract if there is a clear event. Keep original date/time formats. If unsure, use null. 
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

    Do NOT wrap in arrays or extra objects; do NOT add extra keys; do NOT use markdown fences.
    If there is no clear event, don't return anything for this email

    It it possible that one event happens over multiple days; In that case, save the dates and times in a list.
    """

    user_prompt = f"""

    Extract event information from the following email text:

    {email_text}
    """

    contents = f"{system_instruction}\n\n{user_prompt}"

    with open("secrets.json", "r", encoding="utf-8") as f:
        secrets = json.load(f)

    client = genai.Client(api_key=secrets["GEMINI_API_KEY"])

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config={
            "response_mime_type": "application/json",
            "response_schema": SCHEMA_MULTI,
        },
    )

    # resp.text should be a JSON array string: [ {event1}, {event2}, ... ]
    return json.loads(resp.text)

def extract_events_from_all_emails(outdir: str = "data/temp_emails") -> List[dict]:
    """
        This function processes all email text files in the specified folder,
        extracts event information using the LLM, and saves the results
    """

    folder = Path(outdir)
    all_emails_path = folder / "all_emails.txt"

    # 1) Read combined email text
    combined_text = all_emails_path.read_text(encoding="utf-8", errors="strict")

    # 2) Extract events via LLM
    events = extract_event_info_with_llm(combined_text)

    # 3) Convert to DataFrame
    df_results = pd.DataFrame(events)

    # 4) Save to CSV (one row per event)
    output_csv = folder / "extracted_event_info.csv"
    df_results.to_csv(output_csv, index = False)

    print(f"Saved {len(df_results)} events to {output_csv}")

    return events
