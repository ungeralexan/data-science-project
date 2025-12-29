import json
from typing import List, Tuple, Dict, Any

from google import genai

from data.database.database_events import MainEventORM, SubEventORM  # pylint: disable=import-error
from config import DUPLICATION_LLM_MODEL  # pylint: disable=import-error

# Define the expected schema for the LLM response for simple duplicate checking
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

# Define the expected schema for the LLM response for sub_event self-correction
# Returns info about whether a sub_event matches an existing main_event (misclassification)
SUBEVENT_CORRECTION_SCHEMA = {
    "type": "ARRAY",
    "items": {
        "type": "OBJECT",
        "properties": {
            "is_new": {"type": "BOOLEAN", "nullable": False},
            "matches_main_event_id": {"type": "STRING", "nullable": True},
        },
        "required": ["is_new"],
    },
}


def get_event_summary(existing_event, include_event_type: bool = False) -> Dict[str, Any]:
    """Prepare a simplified summary of an existing event for LLM comparison."""
    summary = {
        "id": existing_event.id,
        "Title": existing_event.title,
        "Start_Date": existing_event.start_date,
        "End_Date": existing_event.end_date,
        "Location": existing_event.location,
        "Description": (existing_event.description or "")[:500],
    }
    if include_event_type:
        # Determine if it's a main_event or sub_event based on the ORM class
        if isinstance(existing_event, MainEventORM):
            summary["event_type"] = "main_event"
        else:
            summary["event_type"] = "sub_event"
    return summary


def call_llm_decisions(
    candidates: List[dict],
    existing_summary: List[dict],
    system_instruction: str,
    schema: dict,
) -> List[dict] | None:
    """Shared LLM call helper that returns parsed decisions or None on failure."""
    
    # Build prompt
    user_prompt = f"""
    candidate_events = {json.dumps(candidates, ensure_ascii=False, indent=2)}

    existing_events = {json.dumps(existing_summary, ensure_ascii=False, indent=2)}
    """

    with open("secrets.json", "r", encoding="utf-8") as f:
        secrets = json.load(f)

    client = genai.Client(api_key=secrets["GEMINI_API_KEY"])

    resp = client.models.generate_content(
        model=DUPLICATION_LLM_MODEL,
        contents=f"{system_instruction}\n\n{user_prompt}",
        config={
            "response_mime_type": "application/json",
            "response_schema": schema,
        },
    )

    try:
        parts = resp.candidates[0].content.parts
        text = "".join(getattr(part, "text", "") for part in parts)

        return json.loads(text)
    except json.JSONDecodeError as e:
        print("[event_duplicator] Failed to parse LLM JSON:", e)
        return None


def filter_new_events(
    candidates: List[dict], 
    existing_events: List,
    event_type_name: str
) -> List[dict]:
    """
    Generic function to filter new events (works for both main_events and sub_events).
    Uses a single LLM call to decide which candidate events are new.
    
    candidates: list of dicts from the extractor
    existing_events: list of ORM rows from the DB (MainEventORM or SubEventORM)
    event_type_name: string for logging ("main_event" or "sub_event")
    """

    # If no candidates, return empty list
    if not candidates:
        return []

    # If DB is empty, all candidates are new
    if not existing_events:
        return candidates

    # Prepare a simplified summary of existing events for the LLM
    existing_summary = [get_event_summary(e) for e in existing_events]

    system_instruction = """
    You are an assistant that checks which candidate event(s) are already present
    in a list of existing event(s).

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

    decisions = call_llm_decisions(candidates, existing_summary, system_instruction, BATCH_SCHEMA)

    if not decisions:
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


def filter_new_main_events(
    candidates: List[dict], 
    existing_main_events: List[MainEventORM],
    existing_sub_events: List[SubEventORM]
) -> List[dict]:
    """
    Uses a single LLM call to decide which candidate main_events are new.
    
    IMPORTANT: Compares candidate main_events against BOTH existing main_events AND sub_events.
    This is to catch cases where the LLM incorrectly classified an existing sub_event as a main_event.
    
    Returns only the candidates that are considered new (not duplicates of any existing event).
    """

    # Combine both main_events and sub_events for comparison
    all_existing_events = list(existing_main_events) + list(existing_sub_events)

    new_events = filter_new_events(candidates, all_existing_events, "main_event")
    
    return new_events


def filter_new_sub_events_with_correction(
    candidates: List[dict],
    existing_sub_events: List[SubEventORM],
    existing_main_events: List[MainEventORM]
) -> Tuple[List[dict], List[str]]:
    """
    Uses a single LLM call to decide which candidate sub_events are new.
    Also implements a self-correcting mechanism: if a candidate sub_event matches
    an existing main_event (indicating past misclassification), it returns the
    main_event IDs that should be deleted.
    
    Returns:
        - List of new sub_events to be inserted
        - List of main_event IDs that should be deleted (misclassified events)
    """
    main_events_to_delete: List[str] = []
    
    # If no candidates, return empty results
    if not candidates:
        return [], []

    # If no existing events at all, all candidates are new
    if not existing_sub_events and not existing_main_events:
        return candidates, []

    # First, check candidates against existing sub_events
    new_sub_events = filter_new_events(candidates, existing_sub_events, "sub_event")

    print(f"[filter_new_sub_events_with_correction] After first filter, {len(new_sub_events)} new sub_events remain from {len(candidates)} candidates.")

    # If no new sub_events after first filter, we're done
    if not new_sub_events:
        print("[filter_new_sub_events_with_correction] No new sub_events after initial filtering. Skipping correction check.")
        return [], []
    
    # If no existing main_events, skip the correction check
    if not existing_main_events:
        print("[filter_new_sub_events_with_correction] No existing main_events to check for correction. Skipping correction check.")
        return new_sub_events, []

    print("[filter_new_sub_events_with_correction] Now checking for matches against existing main_events for self-correction.")

    # Now check if any of the "new" sub_events actually match an existing main_event
    # (this would indicate a past misclassification that needs correction)
    existing_main_summary = [get_event_summary(e) for e in existing_main_events]

    system_instruction = """
    You are an assistant that checks if any candidate sub_events match existing main_events.
    
    This is a SELF-CORRECTION check. Sometimes in the past, an event may have been incorrectly
    classified as a main_event when it should have been a sub_event. If a candidate sub_event
    clearly refers to the SAME real-world event as an existing main_event, this indicates
    the main_event was misclassified and should be replaced.

    Consider two events to match if they clearly refer to the SAME real-world event,
    even if there are small wording differences. Use information like:
      - Title similarity (ignoring capitalization and minor wording differences)
      - Date and time
      - Location
      - Description

    You will receive:
      - candidate_sub_events: a JSON array of candidate sub_events
      - existing_main_events: a JSON array of main_events already stored

    For EACH candidate in order:
      - If it matches NO existing main_event: return {"is_new": true, "matches_main_event_id": null}
      - If it matches an existing main_event: return {"is_new": false, "matches_main_event_id": "<the id of the matching main_event>"}

    Return ONLY a JSON ARRAY of objects, same length as `candidate_sub_events`.

    Example:
      [
        {"is_new": true, "matches_main_event_id": null},
        {"is_new": false, "matches_main_event_id": "abc123"},
        {"is_new": true, "matches_main_event_id": null}
      ]

    Do NOT add any extra keys, text or explanations.
    """

    decisions = call_llm_decisions(new_sub_events, existing_main_summary, system_instruction, SUBEVENT_CORRECTION_SCHEMA)

    if not decisions:
        return new_sub_events, []

    if not isinstance(decisions, list) or len(decisions) != len(new_sub_events):
        print(
            f"[filter_new_sub_events_with_correction] LLM output length mismatch. "
            f"Expected {len(new_sub_events)}, got {len(decisions)}."
        )
        return new_sub_events, []

    # Process decisions
    final_new_sub_events: List[dict] = []

    for candidate, decision in zip(new_sub_events, decisions):
        matched_main_id = decision.get("matches_main_event_id")
        
        if matched_main_id:
            # This sub_event matches an existing main_event - this is a correction case
            print(f"[filter_new_sub_events_with_correction] Sub_event {candidate.get('Title')} "
                  f"matches existing main_event ID {matched_main_id} - will correct classification.")
            main_events_to_delete.append(matched_main_id)
            # Add this sub_event to be inserted (it will replace the misclassified main_event)
            final_new_sub_events.append(candidate)
        elif decision.get("is_new", True):
            # Truly new sub_event
            final_new_sub_events.append(candidate)

    print(f"[filter_new_sub_events_with_correction] After correction, {len(final_new_sub_events)} new sub_events to insert. {len(main_events_to_delete)} main_events to delete.")

    return final_new_sub_events, main_events_to_delete
