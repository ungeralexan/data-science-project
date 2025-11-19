# services/event_deduplicator.py
import json
from typing import List

from google import genai

from data.database.database_events import EventORM

DEDUP_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "is_duplicate": {"type": "BOOLEAN", "nullable": False},
    },
    "required": ["is_duplicate"],
}


def is_duplicate_event(candidate: dict, existing_events: List[EventORM]) -> bool:
    """
    Uses LLM to decide whether candidate event is essentially the same as any of the existing events.

    `candidate` is one dict from the LLM extractor (Title, Start_Date, etc.)
    `existing_events` is a list of EventORM rows from the database.
    """
    # If DB is empty, it's definitely not a duplicate
    if not existing_events:
        return False

    # Prepare a compact summary of existing events for the prompt
    existing_summary = []

    for ev in existing_events:
        existing_summary.append(
            {
                "id": ev.id,
                "Title": ev.title,
                "Start_Date": ev.start_date,
                "End_Date": ev.end_date,
                "Location": ev.location,
                "Description": (ev.description or "")[:200],  # I truncate the description to limit the prompt size
            }
        )

    system_instruction = """
    You are an assistant that checks whether a candidate event is already present
    in a list of existing events.

    Consider two events to be duplicates if they clearly refer to the SAME real-world event,
    even if there are small wording differences. Use information like:
      - Title similarity (ignoring capitalization and minor wording differences)
      - Date and time
      - Location
      - Description

    It might be that an event has multiple date and time entries (e.g., a conference over several days).
    In that case a duplicate is one that overlaps ONLY at the exact same set of dates/times. 

    If the candidate clearly matches ANY of the existing events, return:
      {"is_duplicate": true}

    Otherwise, return:
      {"is_duplicate": false}

    Do NOT add any extra keys or text. Only return JSON.
    """

    user_prompt = f"""
    Candidate event:

    {json.dumps(candidate, ensure_ascii=False, indent=2)}

    Existing events:

    {json.dumps(existing_summary, ensure_ascii=False, indent=2)}
    """

    with open("secrets.json", "r", encoding="utf-8") as f:
        secrets = json.load(f)

    client = genai.Client(api_key=secrets["GEMINI_API_KEY"])

    resp = client.models.generate_content(
        model="gemini-2.5-flash",
        
        contents=f"{system_instruction}\n\n{user_prompt}",

        config={
            "response_mime_type": "application/json",
            "response_schema": DEDUP_SCHEMA,
        },
    )

    data = json.loads(resp.text)
    return bool(data.get("is_duplicate"))
