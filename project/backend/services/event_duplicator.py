import json
from typing import List

from google import genai

from data.database.database_events import MainEventORM, SubEventORM  # pylint: disable=import-error
from config import LLM_MODEL  # pylint: disable=import-error

# Define the expected schema for the LLM response
# It should be a list of objects with a single boolean field "is_new"
BATCH_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "is_new": {"type": "BOOLEAN", "nullable": False},
        },
        "required": ["is_new"],
    },
}


def _filter_new_events_generic(
    candidates: List[dict], 
    existing_events: List,
    event_type_name: str
) -> List[dict]:
    """
    Generic function to filter new events (works for both main_events and sub_events).
    Uses a single LLM call to decide which candidate events are new.
    
    `candidates`: list of dicts from the extractor
    `existing_events`: list of ORM rows from the DB (MainEventORM or SubEventORM)
    `event_type_name`: string for logging ("main_event" or "sub_event")
    """

    # If no candidates, return empty list
    if not candidates:
        return []

    # If DB is empty, all candidates are new
    if not existing_events:
        return candidates

    # Prepare a simplified summary of existing events for the LLM
    existing_summary = []

    for existing_event in existing_events:
        existing_summary.append(
            {
                "id": existing_event.id,
                "Title": existing_event.title,
                "Start_Date": existing_event.start_date,
                "End_Date": existing_event.end_date,
                "Location": existing_event.location,
                "Description": (existing_event.description or "")[:500],
            }
        )

    # Prepare the prompt for the LLM
    system_instruction = f"""
    You are an assistant that checks which candidate {event_type_name}s are already present
    in a list of existing {event_type_name}s.

    Consider two events to be duplicates if they clearly refer to the SAME real-world event,
    even if there are small wording differences. Use information like:
      - Title similarity (ignoring capitalization and minor wording differences)
      - Date and time
      - Location
      - Description

    Some events may span multiple days (e.g. a conference). In that case, a duplicate is one
    that overlaps at the same date(s)/time(s), not just vaguely similar.

    You will receive:
      - candidate_events: a JSON array of candidate events
      - existing_events: a JSON array of events already stored

    For EACH candidate in order, decide if it is NEW or already present among existing events.

    Return ONLY a JSON ARRAY of objects, same length as `candidate_events`.
    Each object must have exactly one key: "is_new", a Boolean.

    Example:
      [
        {{"is_new": true}},
        {{"is_new": false}},
        {{"is_new": true}}
      ]

    Do NOT add any extra keys, text or explanations.
    """

    # Prepare the user prompt with the data
    user_prompt = f"""
    candidate_events = {json.dumps(candidates, ensure_ascii=False, indent=2)}

    existing_events = {json.dumps(existing_summary, ensure_ascii=False, indent=2)}
    """

    # Load Gemini API key from secrets.json
    with open("secrets.json", "r", encoding="utf-8") as f:
        secrets = json.load(f)

    # Call the Gemini LLM
    client = genai.Client(api_key=secrets["GEMINI_API_KEY"])

    # Generate the response
    resp = client.models.generate_content(
        model = LLM_MODEL,
        contents = f"{system_instruction}\n\n{user_prompt}",
        config = {
            "response_mime_type": "application/json",
            "response_schema": BATCH_SCHEMA,
        },
    )

    # Parse the LLM response
    try:
        decisions = json.loads(resp.text)

    except json.JSONDecodeError as e:
        print(f"[filter_new_{event_type_name}s] Failed to parse LLM JSON: {e}")
        return candidates

    if not isinstance(decisions, list) or len(decisions) != len(candidates):
        print(
            f"[filter_new_{event_type_name}s] LLM output length mismatch or wrong format. "
            f"Expected {len(candidates)}, got {len(decisions)}."
        )
        return candidates

    # Keep only the candidates marked as new
    new_events: List[dict] = []
    
    for current_candidate, decision in zip(candidates, decisions):
        if bool(decision.get("is_new")):
            new_events.append(current_candidate)

    return new_events


def filter_new_main_events(candidates: List[dict], existing_events: List[MainEventORM]) -> List[dict]:
    """
    Uses a single LLM call to decide which candidate main_events are new.
    Returns only the candidates that are considered new (not duplicates of existing main_events).
    """
    return _filter_new_events_generic(candidates, existing_events, "main_event")


def filter_new_sub_events(candidates: List[dict], existing_events: List[SubEventORM]) -> List[dict]:
    """
    Uses a single LLM call to decide which candidate sub_events are new.
    Returns only the candidates that are considered new (not duplicates of existing sub_events).
    """
    return _filter_new_events_generic(candidates, existing_events, "sub_event")
