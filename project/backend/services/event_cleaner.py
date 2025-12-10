from typing import List
from datetime import datetime, date
from sqlalchemy.orm import Session
from data.database.database_events import EventORM # pylint: disable=import-error

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


def remove_past_events_from_db(db: Session) -> int:
    """
    Remove events from the database that have already passed.
    Returns the number of events removed.
    """
    today = date.today()
    
    # Get all events from DB
    all_events = db.query(EventORM).all()
    removed_count = 0
    
    for event in all_events:
        # Use end_date if available, otherwise start_date
        date_str = event.end_date or event.start_date
        
        if not date_str:
            # No date, keep the event
            continue
        
        parsed_date = parse_date(date_str)
        
        if parsed_date is not None and parsed_date < today:
            print(f"[event_cleaner] Removing past event: '{event.title}' (date: {date_str})")
            db.delete(event)
            removed_count += 1
    
    if removed_count > 0:
        db.commit()
        print(f"[event_cleaner] Removed {removed_count} past events from database.")
    
    return removed_count