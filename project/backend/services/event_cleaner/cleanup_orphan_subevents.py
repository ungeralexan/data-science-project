from sqlalchemy.orm import Session
from data.database.database_events import MainEventORM, SubEventORM # pylint: disable=import-error

def cleanup_orphan_sub_events(db: Session) -> int:
    """
    Delete sub_events that have a main_event_id but the referenced main_event doesn't exist.
    Also delete sub_events without a main_event_id.
    
    Returns the number of orphan sub_events deleted.
    """
    deleted_count = 0
    
    # Get all existing main_event IDs for quick lookup
    existing_main_ids = set(row.id for row in db.query(MainEventORM.id).all())

    # Find orphan sub_events:
    # 1) sub_events with no main_event_id set
    # 2) sub_events whose main_event_id points to a non-existent main_event
    orphan_sub_events = []

    for sub_event in db.query(SubEventORM).all():
        if not sub_event.main_event_id or sub_event.main_event_id not in existing_main_ids:
            orphan_sub_events.append(sub_event)
    
    # Delete orphan sub_events
    for orphan in orphan_sub_events:
        print(f"[event_cleaner] Deleting orphan sub_event: '{orphan.title}' "
              f"(ID: {orphan.id}, references non-existent main_event: {orphan.main_event_id})")
        
        db.delete(orphan)

        deleted_count += 1
    
    if deleted_count > 0:
        db.commit()
        print(f"[event_cleaner] Deleted {deleted_count} orphan sub_events.")
    else:
        print("[event_cleaner] No orphan sub_events found.")
    
    return deleted_count