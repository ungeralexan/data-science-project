import json
from typing import List, Tuple, Dict, Any

from google import genai
from google.genai import types

from data.database.database_events import MainEventORM, SubEventORM  # pylint: disable=import-error
from config import DUPLICATION_LLM_MODEL  # pylint: disable=import-error

# Define the expected schema for the LLM response for simple duplicate checking
# It should be a list of objects with a single boolean field "is_new"
BATCH_SCHEMA = types.Schema(
    type=types.Type.ARRAY,
    items=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "is_new": types.Schema(type=types.Type.BOOLEAN, nullable=False),
        },
        required=["is_new"],
    ),
)

# Schema for main event duplicate checking that also returns existing event info for mapping
MAIN_EVENT_BATCH_SCHEMA = types.Schema(
    type=types.Type.ARRAY,
    items=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "is_new": types.Schema(type=types.Type.BOOLEAN, nullable=False),
            "matching_existing_event_id": types.Schema(type=types.Type.STRING, nullable=True),
        },
        required=["is_new", "matching_existing_event_id"],
    ),
)

# Define the expected schema for the LLM response for sub_event self-correction
# Returns info about whether a sub_event matches an existing main_event (misclassification)
SUBEVENT_CORRECTION_SCHEMA = types.Schema(
    type=types.Type.ARRAY,
    items=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "is_new": types.Schema(type=types.Type.BOOLEAN, nullable=False),
            "matches_main_event_id": types.Schema(type=types.Type.STRING, nullable=True),
            "new_main_event_temp_key": types.Schema(type=types.Type.STRING, nullable=True),
        },
        required=["is_new", "matches_main_event_id", "new_main_event_temp_key"],
    ),
)


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
) -> Tuple[List[dict], Dict[str, str]]:
    """
    Uses a single LLM call to decide which candidate main_events are new.
    
    IMPORTANT: Compares candidate main_events against BOTH existing main_events AND sub_events.
    This is to catch cases where the LLM incorrectly classified an existing sub_event as a main_event.
    
    Returns:
        - List of candidates that are considered new (not duplicates of any existing event)
        - Dict mapping new event temp_keys to existing event temp_keys (for duplicate events)
          This allows new subevents to be linked to existing main events even when temp_keys differ.
    """
    temp_key_mapping: Dict[str, str] = {}  # new_temp_key -> existing_temp_key
    
    if not candidates:
        return [], {}

    # Combine both main_events and sub_events for comparison
    all_existing_events = list(existing_main_events) + list(existing_sub_events)

    # If DB is empty, all candidates are new
    if not all_existing_events:
        return candidates, {}

    # Prepare a simplified summary of existing events for the LLM
    # Include main_event_temp_key for main_events so we can build the mapping
    existing_summary = []

    for e in all_existing_events:
        summary = get_event_summary(e, include_event_type=True)

        # Add main_event_temp_key for main_events
        if isinstance(e, MainEventORM) and e.main_event_temp_key:
            summary["main_event_temp_key"] = e.main_event_temp_key

        existing_summary.append(summary)

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
    Each object must have:
        - "is_new": Boolean - true if the candidate is new, false if it matches an existing event
        - "matching_existing_event_id": String or null - if is_new is false, provide the "id" of 
          the matching existing event; if is_new is true, set to null

    Example:
        [
            {"is_new": true, "matching_existing_event_id": null},
            {"is_new": false, "matching_existing_event_id": "abc123"},
            {"is_new": true, "matching_existing_event_id": null}
        ]

    Do NOT add any extra keys, text or explanations.
    """

    decisions = call_llm_decisions(candidates, existing_summary, system_instruction, MAIN_EVENT_BATCH_SCHEMA)

    # If LLM call failed, process stops and no candidates are treated as new
    if not decisions:
        print("[filter_new_main_events] LLM call failed, stopping pipeline ...")
        return [], {}

    if not isinstance(decisions, list) or len(decisions) != len(candidates):
        print(
            f"[filter_new_main_events] LLM output length mismatch or wrong format. "
            f"Expected {len(candidates)}, got {len(decisions)}."
            f"Stopping pipeline ..."
        )

        return [], {}

    # Build a lookup from existing event ID to its temp_key
    existing_id_to_temp_key: Dict[str, str] = {}

    for e in existing_main_events:
        if e.main_event_temp_key:
            existing_id_to_temp_key[str(e.id)] = e.main_event_temp_key

    # Keep only the candidates marked as new, and build temp_key mapping for duplicates
    new_events: List[dict] = []
    
    # Process decisions
    for current_candidate, decision in zip(candidates, decisions):

        # If new, keep it
        if bool(decision.get("is_new")):
            new_events.append(current_candidate)

        # If duplicate, build temp_key mapping
        else:
            # This candidate is a duplicate - build the temp_key mapping
            matching_id = decision.get("matching_existing_event_id")
            candidate_temp_key = current_candidate.get("Main_Event_Temp_Key")
            
            if matching_id and candidate_temp_key:

                # Find the existing temp_key for the matching event
                existing_temp_key = existing_id_to_temp_key.get(str(matching_id))

                # Only add to mapping if temp_keys differ
                if existing_temp_key and existing_temp_key != candidate_temp_key:

                    temp_key_mapping[candidate_temp_key] = existing_temp_key

                    print(f"[filter_new_main_events] Mapping temp_key '{candidate_temp_key}' -> '{existing_temp_key}' "
                          f"(candidate '{current_candidate.get('Title')}' matches existing event ID {matching_id})")

    return new_events, temp_key_mapping


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

    I) DEFINITION OF AN EVENT:

    I.1) An event is a scheduled occurrence.
    I.2) There are main events and sub events. Main events are the primary events, while sub events are part of a larger event series. (e.g., 
    individual talks in a lecture series, workshops in a conference, sessions in a multi-day event).
    I.3) There cannot be a sub event without a main event!
    
    This is a SELF-CORRECTION check. Sometimes in the past, an event may have been incorrectly
    classified as a main_event when it should have been a sub_event of another main_event. 
    
    If a candidate sub_event clearly refers to the SAME real-world event as an existing main_event, this indicates
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
      - If it matches NO existing main_event: return {"is_new": true, "matches_main_event_id": null, "new_main_event_temp_key": null}
      - If it matches an existing main_event: return {"is_new": false, "matches_main_event_id": "<the id of the matching main_event>", "new_main_event_temp_key": "<the main_event_temp_key of the main_event it should belong to>"}

        As a sub_event always needs a main_event that it belongs to, you MUST provide a new_main_event_temp_key for the sub_event to belong to.
        If you cannot find another suitable main_event for it to belong to, just set new_main_event_temp_key to null.

    Return ONLY a JSON ARRAY of objects, same length as `candidate_sub_events`.

    Example:
      [
        {"is_new": true, "matches_main_event_id": null, "new_main_event_temp_key": null},
        {"is_new": false, "matches_main_event_id": "abc123", "new_main_event_temp_key": "def456"},
        {"is_new": true, "matches_main_event_id": null, "new_main_event_temp_key": null}
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

            # Update the candidate to link to the new main_event_temp_key
            candidate["Main_Event_Temp_Key"] = decision.get("new_main_event_temp_key")

            # Add this sub_event to be inserted (it will replace the misclassified main_event)
            final_new_sub_events.append(candidate)
        elif decision.get("is_new", True):
            # Truly new sub_event
            final_new_sub_events.append(candidate)

    print(f"[filter_new_sub_events_with_correction] After correction, {len(final_new_sub_events)} new sub_events to insert. {len(main_events_to_delete)} main_events to delete.")

    return final_new_sub_events, main_events_to_delete
