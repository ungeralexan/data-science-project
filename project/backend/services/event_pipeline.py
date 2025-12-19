import json
from typing import List, Dict
from pathlib import Path

from sqlalchemy.orm import Session

from data.database.database_events import SessionLocal, MainEventORM, SubEventORM  # pylint: disable=import-error
from config import EMAIL_TEMP_DIR, EMAIL_PIPELINE_DEFAULT_LIMIT  # pylint: disable=import-error

from services.email_downloader import download_latest_emails   # pylint: disable=import-error
from services.event_duplicator import filter_new_main_events, filter_new_sub_events  # pylint: disable=import-error
from services.event_recognizer import extract_event_info_with_llm  # pylint: disable=import-error
from services.event_cleaner import filter_future_events_with_subevents, archive_past_events_in_db  # pylint: disable=import-error
from services.event_recommender import run_event_recommendations  # pylint: disable=import-error

def run_email_to_db_pipeline(limit: int = EMAIL_PIPELINE_DEFAULT_LIMIT, outdir: str = EMAIL_TEMP_DIR) -> None:
    """
    Runs the pipeline to download emails, extract events, and insert them into the database.
    Also removes past events from the database and generates event recommendations for users.
    """

    # 1) Archive past events in database first
    print("[pipeline] Archiving past events in database...")
    with SessionLocal() as db:
        archive_past_events_in_db(db)

    # 2) Downloads latest emails
    print("[pipeline] Downloading latest emails...")
    download_latest_emails(limit=limit)

    # 3) Reads combined text file
    all_emails_path = Path(outdir) / "all_emails.txt"

    if not all_emails_path.exists():
        print("[pipeline] No combined email file created.")
        return

    combined_text = all_emails_path.read_text(encoding="utf-8")

    # 4) Extracts events via LLM
    try:
        print("[pipeline] Extracting events via LLM...")
        events_raw = extract_event_info_with_llm(combined_text)
        print(f"[pipeline] LLM returned {len(events_raw)} events.")
    except Exception as e: # pylint: disable=broad-except
        print(f"[pipeline] Error during event extraction: {e}")
        return

    # 5) Separate main_events and sub_events, then filter out past events
    print("[pipeline] Separating and filtering events...")
    main_events_raw = [e for e in events_raw if e.get("Event_Type") == "main_event"]
    sub_events_raw = [e for e in events_raw if e.get("Event_Type") == "sub_event"]
    print(f"[pipeline] Found {len(main_events_raw)} main_events and {len(sub_events_raw)} sub_events.")
    
    main_events_raw_filtered, sub_events_raw_filtered = filter_future_events_with_subevents(main_events_raw, sub_events_raw)
    print(f"[pipeline] After filtering: {len(main_events_raw_filtered)} main_events and {len(sub_events_raw_filtered)} sub_events remaining.")

    # 6) Opens DB session and insert non-duplicates
    with SessionLocal() as db:
        print("[pipeline] Inserting non-duplicate events...")
        insert_non_duplicate_events(db, main_events_raw_filtered, sub_events_raw_filtered)
        
    # 7) Generate event recommendations for users based on their interests
    print("[pipeline] Generating event recommendations for users...")
    with SessionLocal() as db:
        run_event_recommendations(db)


def insert_non_duplicate_events(db: Session, main_events_raw: List[dict], sub_events_raw: List[dict]) -> None:
    """
    Inserts events into DB, skipping duplicates based on a *single* batch LLM call.
    Handles both main_events and sub_events properly.
    """
    # Exit if no events to insert
    if not main_events_raw and not sub_events_raw:
        print("[insert_non_duplicate_events] No events to insert.")
        return

    # Separate main_events and sub_events
    print(f"[insert_non_duplicate_events] Processing {len(main_events_raw)} main_events and {len(sub_events_raw)} sub_events.")

    # Fetch existing events from DB
    existing_main_events = db.query(MainEventORM).all()
    existing_sub_events = db.query(SubEventORM).all()

    # 1) Ask LLM which main_events are new
    try:
        new_main_events_raw = filter_new_main_events(main_events_raw, existing_main_events)
    except Exception as e: # pylint: disable=broad-except
        print(f"[insert_non_duplicate_events] Error in main_event dedup: {e}")
        new_main_events_raw = main_events_raw

    print(f"[insert_non_duplicate_events] {len(new_main_events_raw)} main_events considered new by LLM.")

    # 2) Ask LLM which sub_events are new
    try:
        new_sub_events_raw = filter_new_sub_events(sub_events_raw, existing_sub_events)
    except Exception as e: # pylint: disable=broad-except
        print(f"[insert_non_duplicate_events] Error in sub_event dedup: {e}")
        new_sub_events_raw = sub_events_raw

    print(f"[insert_non_duplicate_events] {len(new_sub_events_raw)} sub_events considered new by LLM.")

    # 3) Insert main_events first (we need their IDs for sub_events)
    # Build a mapping from temp_key to DB id for linking sub_events
    temp_key_to_main_id: Dict[str, int] = {}
    inserted_main_count = 0

    for event in new_main_events_raw:

        # Skip events without a title
        title = event.get("Title")
        if not title:
            continue

        # Handle missing end date by using start date
        start_date_str = event.get("Start_Date") or ""
        end_date_str = event.get("End_Date") or start_date_str

        new_row = MainEventORM(
            title = title,
            start_date = start_date_str,
            end_date = end_date_str,
            start_time = event.get("Start_Time"),
            end_time = event.get("End_Time"),
            description = event.get("Description"),
            location = event.get("Location") or "",
            street = event.get("Street"),
            house_number = event.get("House_Number"),
            zip_code = event.get("Zip_Code"),
            city = event.get("City"),
            country = event.get("Country"),
            room = event.get("Room"),
            floor = event.get("Floor"),
            speaker = event.get("Speaker"),
            organizer = event.get("Organizer"),
            registration_needed = event.get("Registration_Needed"),
            url = event.get("URL"),
            image_key = event.get("Image_Key"),
            main_event_temp_key = event.get("Main_Event_Temp_Key"),
            sub_event_ids = [],  # JSON column expects list; updated after sub_events are inserted
        )

        db.add(new_row)
        db.flush()  # Get the ID immediately

        # Store temp_key -> ID mapping
        temp_key = event.get("Main_Event_Temp_Key")

        if temp_key:
            temp_key_to_main_id[temp_key] = new_row.id

        inserted_main_count += 1

    db.commit()
    print(f"[insert_non_duplicate_events] Inserted {inserted_main_count} new main_events into DB.")

    # 4) Insert sub_events and link to main_events
    inserted_sub_count = 0
    main_event_sub_ids: Dict[int, list] = {}  # Track which sub_events belong to which main_event

    for event in new_sub_events_raw:

        # Skip events without a title
        title = event.get("Title")
        if not title:
            continue

        # Find the main_event_id from temp_key
        main_event_temp_key = event.get("Main_Event_Temp_Key")
        main_event_id = temp_key_to_main_id.get(main_event_temp_key) if main_event_temp_key else None

        # Handle missing end date by using start date
        start_date_str = event.get("Start_Date") or ""
        end_date_str = event.get("End_Date") or start_date_str

        new_row = SubEventORM(
            title = title,
            start_date = start_date_str,
            end_date = end_date_str,
            start_time = event.get("Start_Time"),
            end_time = event.get("End_Time"),
            description = event.get("Description"),
            location = event.get("Location") or "",
            street = event.get("Street"),
            house_number = event.get("House_Number"),
            zip_code = event.get("Zip_Code"),
            city = event.get("City"),
            country = event.get("Country"),
            room = event.get("Room"),
            floor = event.get("Floor"),
            speaker = event.get("Speaker"),
            organizer = event.get("Organizer"),
            registration_needed = event.get("Registration_Needed"),
            url = event.get("URL"),
            image_key = event.get("Image_Key"),
            main_event_id = main_event_id,
        )

        db.add(new_row)
        db.flush()

        # Track sub_event IDs for each main_event
        if main_event_id:
            if main_event_id not in main_event_sub_ids:

                # Initialize list if not present
                main_event_sub_ids[main_event_id] = []

            # Append the new sub_event ID to the main_event's list
            main_event_sub_ids[main_event_id].append(new_row.id)

        inserted_sub_count += 1

    db.commit()
    print(f"[insert_non_duplicate_events] Inserted {inserted_sub_count} new sub_events into DB.")

    # 5) Update main_events with their sub_event_ids
    for main_id, sub_ids in main_event_sub_ids.items():

        main_event = db.query(MainEventORM).filter(MainEventORM.id == main_id).first()

        if main_event:

            # Merge with existing sub_event_ids if any (JSON column may return list or string)
            existing_ids = main_event.sub_event_ids

            # Handle case where existing_ids is a JSON string
            if isinstance(existing_ids, str):
                try:
                    existing_ids = json.loads(existing_ids)
                except Exception: # pylint: disable=broad-except
                    existing_ids = []

            # Handle case where existing_ids is None
            if existing_ids is None:
                existing_ids = []

            # Combine existing and new sub_event IDs
            all_ids = existing_ids + sub_ids
            main_event.sub_event_ids = all_ids

    db.commit()
    print("[insert_non_duplicate_events] Updated main_events with sub_event_ids.")
