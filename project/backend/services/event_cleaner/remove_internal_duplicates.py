import json

from google import genai
from sqlalchemy.orm import Session

from data.database.database_events import MainEventORM, SubEventORM # pylint: disable=import-error
from config import RECOGNITION_LLM_MODEL  # pylint: disable=import-error

# Schema for internal duplicate detection - returns list of duplicate group indices
from google.genai import types

INTERNAL_DUPLICATE_SCHEMA = types.Schema(
    type=types.Type.ARRAY,
    items=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "duplicate_group": types.Schema(
                type=types.Type.INTEGER,
                nullable=True,
            ),
        },
        required=["duplicate_group"],
    ),
)

# Schema for cross-table duplicate detection - returns which main_event each sub_event duplicates
CROSS_TABLE_DUPLICATE_SCHEMA = types.Schema(
    type=types.Type.ARRAY,
    items=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "is_duplicate_of_sub_event_index": types.Schema(
                type=types.Type.INTEGER,
                nullable=True,
            ),
        },
        required=["is_duplicate_of_sub_event_index"],
    ),
)

def get_event_summary_wo_main_event_id(event) -> str:
    """Create a summary string for an event for duplicate detection."""

    return (
        f"ID: {event.id}, "
        f"Title: {event.title}, "
        f"Start Date: {event.start_date}, "
        f"End Date: {event.end_date}, "
        f"Start Time: {event.start_time}, "
        f"End Time: {event.end_time}, "
        f"Location: {event.location}, "
        f"Description: {event.description[:200] if event.description else 'N/A'}"
    )

def get_event_summary_with_main_event_id(event) -> str:
    """Create a summary string for an event for duplicate detection."""

    return (
        f"ID: {event.id}, "
        f"Title: {event.title}, "
        f"Start Date: {event.start_date}, "
        f"End Date: {event.end_date}, "
        f"Start Time: {event.start_time}, "
        f"End Time: {event.end_time}, "
        f"Location: {event.location}, "
        f"Description: {event.description[:200] if event.description else 'N/A'}, "
        f"main_event_id: {event.main_event_id}"
    )


def call_llm_for_internal_duplicates(events_list: list, table_name: str) -> list:
    """
    Call the LLM to identify duplicate groups within a list of events.
    
    Returns a list of dictionaries with 'duplicate_group' field.
    Events with the same duplicate_group value are duplicates of each other.
    Events with duplicate_group=None are unique.
    """

    if not events_list:
        return []
    
    events_text = "\n".join([
        f"[{i}] {get_event_summary_wo_main_event_id(event)}"
        for i, event in enumerate(events_list)
    ])
    
    prompt = f"""You are an assistant that identifies duplicate events within a database table.

    Below is a list of events from the '{table_name}' table. Your task is to identify which events 
    are duplicates of each other. Here are some guidelines:

    - Events are duplicates if they refer to the same real-world event, even if some details differ slightly (e.g., minor differences in title wording).
    - Events are NOT duplicates if they refer to different occurrences of a recurring event (e.g., same title but different dates).
    - Put special emphasis on matching dates, times, locations, and core titles when determining duplicates. This is important because events with similar titles but different dates are often NOT duplicates.
    - If a single event has multiple start or end dates/times listed, and any of those matches another event's date/time in addition to other matching details, consider them duplicates even if the other dates/times differ.

    Here are the events:
    {events_text}
    
    For each event, assign a 'duplicate_group' number:
    - Events that are duplicates of each other should have the SAME duplicate_group number
    - Events that are unique (not duplicates of anything) should have duplicate_group = null
    - Start duplicate group numbering from 1

    Return a JSON array with one object per event (in the same order), each containing:
    - "duplicate_group": integer (for duplicates) or null (for unique events)

    Example: If events [0], [2], [5] are duplicates and [1], [3] are duplicates:
    [
        {{"duplicate_group": 1}}, 
        {{"duplicate_group": 2}}, 
        {{"duplicate_group": 1}}, 
        {{"duplicate_group": 2}}, 
        {{"duplicate_group": null}}, 
        {{"duplicate_group": 1}}
    ]
    """
    
    with open("secrets.json", "r", encoding="utf-8") as f:
        secrets = json.load(f)

    client = genai.Client(api_key=secrets["GEMINI_API_KEY"])

    response = client.models.generate_content(
        model=RECOGNITION_LLM_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": INTERNAL_DUPLICATE_SCHEMA,
        },
    )
    
    # Try to get text from response.text first, then fallback to extracting from candidates
    response_text = response.text
    
    if response_text is None and hasattr(response, 'candidates') and response.candidates:
        # Try to extract text directly from candidates
        parts = response.candidates[0].content.parts if response.candidates[0].content else []
        response_text = "".join(getattr(part, "text", "") for part in parts)
        if response_text:
            print(f"[event_cleaner] Extracted text from candidates for {table_name}")
    
    if not response_text:
        # Log additional details to understand why the response is empty
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            print(f"[event_cleaner] Prompt feedback: {response.prompt_feedback}")
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'finish_reason'):
                    print(f"[event_cleaner] Candidate finish reason: {candidate.finish_reason}")
                if hasattr(candidate, 'safety_ratings'):
                    print(f"[event_cleaner] Safety ratings: {candidate.safety_ratings}")
        print(f"[event_cleaner] Warning: LLM returned empty response for {table_name} duplicate detection")
        return []
    
    return json.loads(response_text)

def delete_internal_duplicates(db: Session, llm_results, considered_events, event_type: str) -> tuple[int, int]:
    """
    Delete duplicates inside one table and report how many items were removed.

    Returns
    -------
    (deleted_count, cascaded_sub_events)
        deleted_count: number of rows explicitly deleted for this table.
        cascaded_sub_events: number of sub_events removed implicitly because their parent
        main_event was deleted (only populated when event_type == "main_event").

    duplicate_groups will look like this:
       
    {
        1: [event1, event2, event5],
        2: [event3, event4],
        ...
    }
    """
    duplicate_groups = {}
    total_deleted = 0
    cascaded_sub_events = 0

    # Group events by their duplicate_group
    for i, result in enumerate(llm_results):

        group = result.get("duplicate_group")

        # Only consider events assigned to a duplicate group
        if group is not None:

            # Initialize the group in the dictionary if not already present
            if group not in duplicate_groups:
                duplicate_groups[group] = []

            # Append event to its duplicate group
            duplicate_groups[group].append(considered_events[i])
   
    if not duplicate_groups:
        print(f"[event_cleaner] No duplicate {event_type} groups found.")
        return total_deleted, cascaded_sub_events

    # Delete all but the first event in each duplicate group
    for _, events in duplicate_groups.items():

        if len(events) > 1:
            # Keep the first one (lowest ID), delete the rest

            events_to_delete = events[1:]

            for event in events_to_delete:
                if event_type == "main_event":
                    cascaded_sub_events += len(event.sub_events or [])

                print(f"[event_cleaner] Deleting duplicate {event_type}: '{event.title}' "
                        f"(ID: {event.id}, duplicate of ID: {events[0].id})")
                
                db.delete(event)

                total_deleted = total_deleted + 1
        elif len(events) == 1:
            print(f"[event_cleaner] Warning: Duplicate group with only one event found for {event_type} ID: {events[0].id}")
        else:
            print(f"[event_cleaner] Warning: Empty duplicate group found for {event_type}.")

    db.commit()

    return total_deleted, cascaded_sub_events

def cleanup_internal_duplicates(db: Session):
    """
    Find and remove duplicate events within the main_events and sub_events tables.
    
    Uses an LLM to identify events that are duplicates of each other within the same table.
    For each group of duplicates, keeps only the first occurrence (lowest ID) and deletes the rest.
    
    Returns the total number of deleted duplicate events.
    """

    main_events_deleted = 0
    cascaded_sub_events_from_mains = 0
    sub_events_deleted = 0
    
    # Process main_events table
    main_events = db.query(MainEventORM).filter(
        MainEventORM.archived_event == False  # pylint: disable=singleton-comparison
    ).order_by(MainEventORM.id).all()

    if main_events:
        print(f"[event_cleaner] Analyzing {len(main_events)} main_events for internal duplicates...")
        print("")
        
        try:
            llm_main_event_results = call_llm_for_internal_duplicates(main_events, "main_events")
            main_events_deleted, cascaded_sub_events_from_mains = delete_internal_duplicates(db, llm_main_event_results, main_events, "main_event")
                        
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[event_cleaner] Error analyzing main_events duplicates: {e}")
            print("")
    else:
        print("[event_cleaner] No main_events found to analyze for duplicates.")
        print("")
    
    # Process sub_events table
    sub_events = db.query(SubEventORM).filter(
        SubEventORM.archived_event == False  # pylint: disable=singleton-comparison
    ).order_by(SubEventORM.id).all()
    
    if sub_events:
        print("")
        print(f"[event_cleaner] Analyzing {len(sub_events)} sub_events for internal duplicates...")
        print("")
        
        try:
            llm_sub_event_results = call_llm_for_internal_duplicates(sub_events, "sub_events")
            sub_events_deleted, _ = delete_internal_duplicates(db, llm_sub_event_results, sub_events, "sub_event")
                        
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"[event_cleaner] Error analyzing sub_events duplicates: {e}")
            print("")
    else:
        print("[event_cleaner] No sub_events found to analyze for duplicates.")
        print("")

    total_deleted_rows = main_events_deleted + sub_events_deleted

    if total_deleted_rows > 0 or cascaded_sub_events_from_mains > 0:
        print("")
        print(
            f"[event_cleaner] Deleted {main_events_deleted} main_event duplicates "
            f"(cascaded {cascaded_sub_events_from_mains} sub_events) "
            f"and {sub_events_deleted} sub_event duplicates."
        )
    else:
        print("[event_cleaner] No internal duplicates found.")


def call_llm_for_cross_table_duplicates(main_events: list, sub_events: list) -> list:
    """
    Call the LLM to identify sub_events that are duplicates of main_events.
    
    Each sub_event has a main_event_id pointing to its parent main_event.
    The LLM should NOT compare a sub_event with its parent main_event.
    
    Returns a list of dictionaries with 'is_duplicate_of_main_event_index' field.
    If a sub_event is a duplicate of a main_event, the index (0-based) of that main_event is returned.
    If a sub_event is not a duplicate of any main_event, null is returned.
    """

    if not main_events or not sub_events:
        return []
    
    # Build the main events list with indices
    main_events_text = "\n".join([f"[MAIN_{event.id}] {get_event_summary_wo_main_event_id(event)}" for _, event in enumerate(main_events)])
    
    # Build the sub events list, noting which main_event comparisons to skip
    sub_events_lines = []

    for _, sub_event in enumerate(sub_events):
        summary = get_event_summary_with_main_event_id(sub_event)
        
        # Find the parent main_event index to exclude from comparison
        parent_main_idx = sub_event.main_event_id
        
        if parent_main_idx is not None:
            sub_events_lines.append(
                f"[SUB_{sub_event.id}] {summary} (SKIP comparison with MAIN_{parent_main_idx} - it's the parent)"
            )
        else:
            sub_events_lines.append(f"[SUB_{sub_event.id}] {summary}")
    
    sub_events_text = "\n".join(sub_events_lines)
    
    prompt = f"""You are an assistant that identifies duplicate events across two database tables.

    Below are events from the 'main_events' table and the 'sub_events' table. 
    Your task is to identify which main_events are duplicates of sub_events (same event, possibly with slight variations).

    IMPORTANT: When a sub_event says "(SKIP comparison with MAIN_X - it's the parent)", do NOT consider 
    that sub_event as a duplicate of MAIN_X. They are parent-child relationships, not duplicates.
    Only mark a main_event as a duplicate if it matches a DIFFERENT sub_event.

    Guidelines for identifying duplicates:
    - Events are duplicates if they refer to the same real-world event, even if some details differ slightly.
    - Events are NOT duplicates if they refer to different occurrences of a recurring event (same title but different dates).
    - Put special emphasis on matching dates, times, locations, and core titles.
    - If one main event matches multiple sub_events, only consider the first matching sub_event as the duplicate.
    - If a single event has multiple start or end dates/times listed, and any of those matches another event's date/time in addition to other matching details, consider them duplicates even if the other dates/times differ.

    MAIN EVENTS:
    {main_events_text}

    SUB EVENTS:
    {sub_events_text}

    For each main_event (in order), determine if it is a duplicate of any sub_event (Except its children).
    Return a JSON array with one object per main_event, each containing:
    - "is_duplicate_of_sub_event_index": integer (0-based index of the matching sub_event) or null (if not a duplicate)

    Example: If MAIN_0 is a duplicate of SUB_2, and MAIN_1 is unique, and MAIN_2 is a duplicate of SUB_0:

    [
        {{"is_duplicate_of_sub_event_index": 2}}, 
        {{"is_duplicate_of_sub_event_index": null}}, 
        {{"is_duplicate_of_sub_event_index": 0}}
    ]

    """
    
    with open("secrets.json", "r", encoding="utf-8") as f:
        secrets = json.load(f)

    client = genai.Client(api_key=secrets["GEMINI_API_KEY"])

    response = client.models.generate_content(
        model=RECOGNITION_LLM_MODEL,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": CROSS_TABLE_DUPLICATE_SCHEMA,
        },
    )
    
    # Try to get text from response.text first, then fallback to extracting from candidates
    response_text = response.text
    
    if response_text is None and hasattr(response, 'candidates') and response.candidates:
        # Try to extract text directly from candidates
        parts = response.candidates[0].content.parts if response.candidates[0].content else []
        response_text = "".join(getattr(part, "text", "") for part in parts)
        
        if response_text:
            print("[event_cleaner] Extracted text from candidates for cross-table duplicates")
    
    if not response_text:
        # Log additional details to understand why the response is empty
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            print(f"[event_cleaner] Prompt feedback: {response.prompt_feedback}")
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'finish_reason'):
                    print(f"[event_cleaner] Candidate finish reason: {candidate.finish_reason}")
                if hasattr(candidate, 'safety_ratings'):
                    print(f"[event_cleaner] Safety ratings: {candidate.safety_ratings}")

        print("[event_cleaner] Warning: LLM returned empty response for cross-table duplicate detection")
        return []
    
    return json.loads(response_text)


def cleanup_cross_table_duplicates(db: Session) -> int:
    """
    Find and remove sub_events that are duplicates of main_events (excluding parent relationships).
    
    Uses an LLM to identify main_events that are duplicates of sub_events.
    Main_events are NOT compared with their child sub_events (based on main_event_id).
    Duplicate main_events are deleted, keeping the sub_event.
    
    Returns the total number of deleted duplicate main_events.
    """

    print("[event_cleaner] Checking for cross-table duplicates (main_events duplicating sub_events)...")

    total_deleted = 0
    
    # Get all non-archived main_events
    main_events = db.query(MainEventORM).filter(MainEventORM.archived_event == False).order_by(MainEventORM.id).all()
    sub_events = db.query(SubEventORM).filter(SubEventORM.archived_event == False and SubEventORM.main_event_id).order_by(SubEventORM.id).all()
    
    if not main_events or not sub_events:
        print("[event_cleaner] Not enough events to compare across tables.")
        return 0
    
    print(f"[event_cleaner] Comparing {len(sub_events)} sub_events against {len(main_events)} main_events...")
    
    try:
        llm_results = call_llm_for_cross_table_duplicates(main_events, sub_events)
        
        for _, result in enumerate(llm_results):
            sub_event_idx = result.get("is_duplicate_of_sub_event_index")

            if sub_event_idx is not None:

                current_sub_event = db.query(SubEventORM).filter(SubEventORM.id == sub_event_idx).first()
                main_event_to_delete = db.query(MainEventORM).filter(MainEventORM.id == current_sub_event.main_event_id).first()
                
                if main_event_to_delete:
                    print(f"[event_cleaner] Deleting main_event '{main_event_to_delete.title}' "
                          f"(ID: {main_event_to_delete.id}) - duplicate of sub_event '{current_sub_event.title}' "
                          f"(ID: {current_sub_event.id})")
                    
                    db.delete(main_event_to_delete)

                    total_deleted = total_deleted + 1
                    
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"[event_cleaner] Error analyzing cross-table duplicates: {e}")
    
    if total_deleted > 0:
        db.commit() 
        print(f"[event_cleaner] Deleted {total_deleted} cross-table duplicate sub_events.")
    else:
        print("[event_cleaner] No cross-table duplicates found.")
    
    return total_deleted