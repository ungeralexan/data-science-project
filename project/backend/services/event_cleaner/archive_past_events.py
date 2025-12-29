from typing import List, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from data.database.database_events import MainEventORM, SubEventORM # pylint: disable=import-error

def parse_date(date_str: str) -> date | None:
    """
    Parse a date string in various formats and return a date object.
    Returns None if parsing fails.
    """
    if not date_str:
        return None
    
    # Common date formats to try
    formats = [
        "%Y-%m-%d",      # 2025-01-15
        "%d.%m.%Y",      # 15.01.2025
        "%d/%m/%Y",      # 15/01/2025
        "%m/%d/%Y",      # 01/15/2025
        "%B %d, %Y",     # January 15, 2025
        "%b %d, %Y",     # Jan 15, 2025
        "%d %B %Y",      # 15 January 2025
        "%d %b %Y",      # 15 Jan 2025
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    
    return None


def is_future_event(event: dict) -> bool:
    """
    Check if an event is in the future based on its end date (or start date if no end date).
    Returns True if the event is today or in the future, False if it's in the past.
    If date cannot be parsed, returns True.
    """
    today = date.today()
    
    # Prefer end_date, fall back to start_date
    end_date_str = event.get("End_Date") or event.get("Start_Date")
    
    if not end_date_str:
        # No date available, include the event
        return True
    
    parsed_date = parse_date(end_date_str)
    
    if parsed_date is None:
        # Could not parse date, include the event
        return True
    
    return parsed_date >= today


def filter_future_events(events: List[dict]) -> List[dict]:
    """
    Filter a list of events to only include future events.
    """

    future_events = []
    past_count = 0
    
    for event in events:
        if is_future_event(event):
            future_events.append(event)
        else:
            past_count += 1
            title = event.get("Title", "Unknown")
            end_date = event.get("End_Date") or event.get("Start_Date")

            print(f"[event_cleaner] Skipping past event: '{title}' (date: {end_date})")
    
    if past_count > 0:
        print(f"[event_cleaner] Filtered out {past_count} past events.")
    
    return future_events


def filter_future_events_with_subevents(
    main_events: List[dict], 
    sub_events: List[dict]
) -> Tuple[List[dict], List[dict]]:
    """
    Filter main_events and sub_events with special logic:
    - Main_events without sub_events: only keep if they are in the future
    - Main_events with sub_events: keep if ANY of their sub_events is in the future
      (also keep all sub_events of that main_event, including past ones)
    """
    
    # Group sub_events by main_event_temp_key
    sub_events_by_key: dict = {}

    for sub in sub_events:

        # Get the main_event_temp_key
        key = sub.get("Main_Event_Temp_Key", "")

        if key:
            if key not in sub_events_by_key:

                sub_events_by_key[key] = []

            sub_events_by_key[key].append(sub)
    

    filtered_main_events = []
    filtered_sub_events = []
    
    # Process main_events
    for main_event in main_events:

        # Get the main_event_temp_key
        temp_key = main_event.get("Main_Event_Temp_Key", "")
        related_subs = sub_events_by_key.get(temp_key, [])
        
        # If no related sub_events
        if not related_subs:
            # Main_event without sub_events: standard future check
            if is_future_event(main_event):
                filtered_main_events.append(main_event)
            else:
                title = main_event.get("Title", "Unknown")
                end_date = main_event.get("End_Date") or main_event.get("Start_Date")
                print(f"[event_cleaner] Skipping past main_event: '{title}' (date: {end_date})")
        else:
            # Main_event with sub_events: check if ANY sub_event is in the future
            has_future_sub = any(is_future_event(sub) for sub in related_subs)
            
            if has_future_sub:
                # Keep main_event and ALL its sub_events (including past ones)
                filtered_main_events.append(main_event)
                filtered_sub_events.extend(related_subs)
            else:
                # All sub_events are in the past, skip main_event and all sub_events
                title = main_event.get("Title", "Unknown")
                print(f"[event_cleaner] Skipping main_event '{title}' - all sub_events are in the past")
    
    # Also process orphan sub_events (sub_events without a matching main_event)
    processed_keys = set(sub_events_by_key.keys())
    main_event_keys = {m.get("Main_Event_Temp_Key", "") for m in main_events}

    remaining_keys = processed_keys - main_event_keys

    if remaining_keys:
        print(f"[event_cleaner] Processing {len(remaining_keys)} orphan sub_events")
    
        # Only look at orphan sub_events
        for key in remaining_keys:
            for sub in sub_events_by_key[key]:
                if is_future_event(sub):
                    filtered_sub_events.append(sub)
                else:
                    title = sub.get("Title", "Unknown")
                    end_date = sub.get("End_Date") or sub.get("Start_Date")
                    print(f"[event_cleaner] Skipping orphan past sub_event: '{title}' (date: {end_date})")
    
    return filtered_main_events, filtered_sub_events


def archive_past_events_in_db(db: Session) -> int:
    """
    Archive events in the database that have already passed by setting archived_event=True.
    For main_events with sub_events: only archive if ALL sub_events are in the past.
    Returns the total number of events archived.
    """
    today = date.today()
    archived_count = 0
    
    # Get all non-archived main_events from DB
    all_main_events = db.query(MainEventORM).filter(MainEventORM.archived_event == False).all()
    
    for main_event in all_main_events:
        # Get all sub_events for this main_event (including already archived ones for the check)
        sub_events = db.query(SubEventORM).filter(SubEventORM.main_event_id == main_event.id).all()
        
        if not sub_events:
            # Main_event without sub_events: standard past check
            date_str = main_event.end_date or main_event.start_date
            
            if date_str:
                parsed_date = parse_date(date_str)
                if parsed_date is not None and parsed_date < today:
                    print(f"[event_cleaner] Archiving past main_event: '{main_event.title}' (date: {date_str})")
                    main_event.archived_event = True
                    archived_count += 1
        else:
            # Main_event with sub_events: check if ALL sub_events are in the past
            all_subs_past = True
            
            for sub in sub_events:
                date_str = sub.end_date or sub.start_date

                if not date_str:
                    all_subs_past = False
                    break
                    
                parsed_date = parse_date(date_str)

                if parsed_date is None or parsed_date >= today:
                    all_subs_past = False
                    break
            
            if all_subs_past:
                print(f"[event_cleaner] Archiving main_event '{main_event.title}' and all its sub_events - all past")
                # Archive main_event and all its sub_events
                main_event.archived_event = True
                archived_count += 1
                
                for sub in sub_events:
                    if not sub.archived_event:
                        sub.archived_event = True
                        archived_count += 1
    
    # Also archive orphan sub_events that are in the past
    orphan_sub_events = db.query(SubEventORM).filter(
        SubEventORM.main_event_id == None,
        SubEventORM.archived_event == False
    ).all()
    
    for sub in orphan_sub_events:
        date_str = sub.end_date or sub.start_date
        
        if date_str:
            parsed_date = parse_date(date_str)
            if parsed_date is not None and parsed_date < today:
                print(f"[event_cleaner] Archiving past orphan sub_event: '{sub.title}' (date: {date_str})")
                sub.archived_event = True
                archived_count += 1
    
    if archived_count > 0:
        db.commit()
        print(f"[event_cleaner] Archived {archived_count} past events in database.")
    else:
        print("[event_cleaner] No past events to archive in database.")
    
    return archived_count