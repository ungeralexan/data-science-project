import json
from typing import List

from google import genai

from data.database.database_events import EventORM  # pylint: disable=import-error
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

def filter_new_events(candidates: List[dict], existing_events: List[EventORM]) -> List[dict]:
    """
    Uses a single LLM call to decide, for each candidate event, whether it is new
    or already present among existing events. A single call is used as there are call limits when using Gemini.

    Returns only the candidates that are considered new (i.e., not duplicates of existing events in database).

    `candidates`  : list of dicts from the extractor (Title, Start_Date, ...)
    `existing_events`: list of EventORM rows from the DB.
    """

    # If no candidates, return empty list
    if not candidates:
        return []

    # If DB is empty, all candidates are new
    if not existing_events:
        return candidates

    # Prepare a simplified summary of existing events for the LLM
    existing_summary = []

    # I add only key fields to limit the size of the prompt
    for existing_event in existing_events:
        existing_summary.append(
            {
                "id": existing_event.id,
                "Title": existing_event.title,
                "Start_Date": existing_event.start_date,
                "End_Date": existing_event.end_date,
                "Location": existing_event.location,
                "Description": (existing_event.description or "")[:250], # I only send first 250 chars to limit size of prompt
            }
        )

    # Prepare the prompt for the LLM
    system_instruction = """
    You are an assistant that checks which candidate events are already present
    in a list of existing events.

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
        {"is_new": true},
        {"is_new": false},
        {"is_new": true}
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

    # Handle possible parsing errors. In that case, all candidates are treated as new.
    except json.JSONDecodeError as e:
        print(f"[filter_new_events] Failed to parse LLM JSON: {e}")
        return candidates

    # This checks if the output is valid and matches the expected length.
    # If not, all candidates are treated as new.
    if not isinstance(decisions, list) or len(decisions) != len(candidates):
        print(
            "[filter_new_events] LLM output length mismatch or wrong format. "
            f"Expected {len(candidates)}, got {len(decisions)}."
        )
        
        return candidates

    # I keep only the candidates marked as new
    new_events: List[dict] = []
    
    # Collect new events based on LLM decisions
    for current_candidate, decision in zip(candidates, decisions):

        # If marked as new, keep it
        if bool(decision.get("is_new")):
            new_events.append(current_candidate)

    # Return the filtered list of new events
    return new_events
