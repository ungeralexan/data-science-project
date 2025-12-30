import json
from typing import List, Dict
from pathlib import Path
import logging

import pandas as pd

from sqlalchemy.orm import Session

from data.database.database_events import SessionLocal, MainEventORM, SubEventORM  # pylint: disable=import-error
from config import EMAIL_TEMP_DIR, EMAIL_PIPELINE_DEFAULT_LIMIT  # pylint: disable=import-error

from services.email_downloader.email_downloader import download_latest_emails   # pylint: disable=import-error
from services.event_duplicator import filter_new_main_events, filter_new_sub_events_with_correction  # pylint: disable=import-error
from services.event_recognizer import extract_event_info_with_llm  # pylint: disable=import-error

from services.event_cleaner.archive_past_events import filter_future_events_with_subevents, archive_past_events_in_db  # pylint: disable=import-error
from services.event_cleaner.cleanup_orphan_subevents import cleanup_orphan_sub_events  # pylint: disable=import-error
from services.event_cleaner.remove_internal_duplicates import cleanup_internal_duplicates, cleanup_cross_table_duplicates  # pylint: disable=import-error

from services.event_recommender import run_event_recommendations  # pylint: disable=import-error

logging.getLogger("google_genai.types").setLevel(logging.ERROR)

def run_email_to_db_pipeline(limit: int = EMAIL_PIPELINE_DEFAULT_LIMIT, outdir: str = EMAIL_TEMP_DIR) -> None:
    """
    Runs the pipeline to download emails, extract events, and insert them into the database.
    Also removes past events from the database and generates event recommendations for users.
    """

    print("##############################################################################################")
    print("")
    print("EMAIL TO DB PIPELINE [event_pipeline.py]")
    print("")
    print("Step 1: Remove internal duplicates from DB [remove_internal_duplicates.py]")
    print("Step 2: Remove cross-table duplicates from DB [remove_internal_duplicates.py]")
    print("Step 3: Archive past events in DB [archive_past_events.py]")
    print("Step 4: Cleanup orphan sub_events [cleanup_orphan_subevents.py]")
    print("Step 5: Download latest emails [email_downloader.py]")
    print("Step 6: Extract events via LLM [event_recognizer.py]")
    print("Step 7: Separate main_events and sub_events, filter out past events [archive_past_events.py]")
    print("Step 8: Insert non-duplicate events into DB [event_duplicator.py]")
    print("Step 9: Generate event recommendations for users [event_recommender.py]")
    print("")
    print("##############################################################################################")


    # 1) Remove internal duplicates from existing database tables
    print("________________________________________________________________________________________________")
    print("")
    print("[pipeline] Removing internal duplicates from DB [event_cleaner.py]...")
    print("")

    with SessionLocal() as db:
        cleanup_internal_duplicates(db)
        db.close()

    # 2) Remove cross-table duplicates (sub_events that duplicate main_events)
    print("________________________________________________________________________________________________")
    print("")
    print("[pipeline] Removing cross-table duplicates from DB [event_cleaner.py]...")
    print("")

    with SessionLocal() as db:
        cleanup_cross_table_duplicates(db)
        db.close()

    # 3) Archive past events in database first
    print("________________________________________________________________________________________________")
    print("")
    print("[pipeline] Archiving past events in database [event_cleaner.py]...")
    print("")

    with SessionLocal() as db:
        archive_past_events_in_db(db)
        db.close()

    # 4) Cleanup orphan sub_events (sub_events whose main_event doesn't exist)
    print("________________________________________________________________________________________________")
    print("")
    print("[pipeline] Cleaning up orphan sub_events [event_cleaner.py]...")
    print("")

    with SessionLocal() as db:
        cleanup_orphan_sub_events(db)
        db.close()

    # 5) Downloads latest emails
    print("________________________________________________________________________________________________")
    print("")
    print("[pipeline] Downloading latest emails [email_downloader.py]...")
    print("")

    download_latest_emails(limit=limit)

    all_emails_path = Path(outdir) / "all_emails.txt"

    if not all_emails_path.exists():
        print("[pipeline] No combined email file created.")
        return

    combined_text = all_emails_path.read_text(encoding="utf-8")

    # 6) Extracts events via LLM
    print("________________________________________________________________________________________________")
    print("")
    print("[pipeline] Extracting events via LLM [event_recognizer.py]...")
    print("")

    try:
        events_raw = extract_event_info_with_llm(combined_text)
        print(f"[pipeline] LLM returned {len(events_raw)} events.")
    except Exception as e: # pylint: disable=broad-except
        print(f"[pipeline] Error during event extraction: {e}")
        return

    # 7) Separate main_events and sub_events, then filter out past events
    print("________________________________________________________________________________________________")
    print("")
    print("[pipeline] Separating and filtering events to only include future events [event_cleaner.py]...")
    print("")

    main_events_raw = [e for e in events_raw if e.get("Event_Type") == "main_event"]
    sub_events_raw = [e for e in events_raw if e.get("Event_Type") == "sub_event"]
    none_event_raw = [e for e in events_raw if e.get("Event_Type") not in ["main_event", "sub_event"]]

    print(f"[pipeline] Found {len(main_events_raw)} main_events and {len(sub_events_raw)} sub_events.")
    
    if none_event_raw:
        print(f"[pipeline] Warning: {len(none_event_raw)} events with unknown Event_Type found and will be ignored.")
    
    main_events_raw_filtered, sub_events_raw_filtered = filter_future_events_with_subevents(main_events_raw, sub_events_raw)
    print(f"[pipeline] After future filtering: {len(main_events_raw_filtered)} main_events and {len(sub_events_raw_filtered)} sub_events remaining.")

    # 8) Opens DB session and insert non-duplicates
    print("________________________________________________________________________________________________")
    print("")
    print("[pipeline] Starting duplicate check [event_duplicator.py]...")
    print("")
    with SessionLocal() as db:
        insert_non_duplicate_events(db, main_events_raw_filtered, sub_events_raw_filtered)
        db.close()
        
    # 9) Generate event recommendations for users based on their interests
    print("________________________________________________________________________________________________")
    print("")
    print("[pipeline] Generating event recommendations for users [event_recommender.py]...")
    print("")

    with SessionLocal() as db:
        run_event_recommendations(db)
        db.close()

    print("##############################################################################################")
    print("")
    print("[pipeline] EMAIL TO DB PIPELINE completed!")
    print("")
    print("##############################################################################################")


def insert_non_duplicate_events(db: Session, main_events_raw: List[dict], sub_events_raw: List[dict]) -> None:
    """
    Inserts events into DB, skipping duplicates based on a *single* batch LLM call.
    Handles both main_events and sub_events properly.
    """
    # Exit if no events to insert
    if not main_events_raw and not sub_events_raw:
        print("[pipeline] No events to insert.")
        return

    # Separate main_events and sub_events
    print(f"[pipeline] Processing {len(main_events_raw)} potentially new main_events and {len(sub_events_raw)} potentially new sub_events.")

    # Fetch existing events from DB
    existing_main_events = db.query(MainEventORM).filter(MainEventORM.archived_event == False).all()
    existing_sub_events = db.query(SubEventORM).filter(SubEventORM.archived_event == False).all()

    print(f"[pipeline] There are {len(existing_main_events)} existing main_events and {len(existing_sub_events)} existing sub_events.")

    # 1) Ask LLM which main_events are new (compares against BOTH main_events AND sub_events)
    print("")
    print("[pipeline] Checking for new main_events via LLM...")

    try:
        new_main_events_raw = filter_new_main_events(main_events_raw, existing_main_events, existing_sub_events)
        print(f"[pipeline] {len(new_main_events_raw)} main_events considered new by LLM.")
    except Exception as e: # pylint: disable=broad-except
        print(f"[pipeline] Error while checking for new main_events via LLM: {e}")
        print("[pipeline] Proceeding by assuming all main_events are new.")

        new_main_events_raw = main_events_raw

    # 2) Ask LLM which sub_events are new, also check for misclassified main_events
    main_events_to_delete: List[str] = []
    
    print("")
    print("[pipeline] Checking for new sub_events via LLM...")

    try:
        new_sub_events_raw, main_events_to_delete = filter_new_sub_events_with_correction(sub_events_raw, existing_sub_events, existing_main_events)
        print(f"[pipeline] {len(new_sub_events_raw)} sub_events considered new by LLM.")
    except Exception as e: # pylint: disable=broad-except
        print(f"[pipeline] Error while checking for new sub_events via LLM: {e}")
        print("[pipeline] Proceeding by assuming all sub_events are new.")

        new_sub_events_raw = sub_events_raw

    # 2.1) Delete misclassified main_events (events that were wrongly classified as main_events but are actually sub_events)
    print("")

    if main_events_to_delete:
        print(f"[pipeline] Deleting {len(main_events_to_delete)} misclassified main_events...")

        for main_event_id in main_events_to_delete:
            main_event = db.query(MainEventORM).filter(MainEventORM.id == main_event_id).first()

            if main_event:
                print(f"[pipeline] Deleting misclassified main_event: '{main_event.title}' (ID: {main_event_id})")

                db.delete(main_event)

        db.commit()
        
        print(f"[pipeline] Deleted {len(main_events_to_delete)} misclassified main_events.")
    else:
        print("[pipeline] No misclassified main_events to delete.")

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
            language = event.get("Language"),
            speaker = event.get("Speaker"),
            organizer = event.get("Organizer"),
            registration_needed = event.get("Registration_Needed"),
            url = event.get("URL"),
            registration_url = event.get("Registration_URL"),
            meeting_url = event.get("Meeting_URL"),
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

    print(f"[pipeline] Inserted {inserted_main_count} new main_events into DB.")

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
            language = event.get("Language"),
            speaker = event.get("Speaker"),
            organizer = event.get("Organizer"),
            registration_needed = event.get("Registration_Needed"),
            url = event.get("URL"),
            registration_url = event.get("Registration_URL"),
            meeting_url = event.get("Meeting_URL"),
            image_key = event.get("Image_Key"),
            main_event_temp_key = event.get("Main_Event_Temp_Key"),
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
    print(f"[pipeline] Inserted {inserted_sub_count} new sub_events into DB.")

    # 5) Update main_events with their sub_event_ids and propagate registration_needed from sub_events
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

            # Check if any sub_event requires registration, if so, update main_event's registration_needed
            sub_events = db.query(SubEventORM).filter(SubEventORM.main_event_id == main_id).all()
            for sub_event in sub_events:
                # Check if sub_event has registration_url (implies registration needed)
                # or if registration_needed is explicitly True or "true"
                sub_reg_needed = sub_event.registration_needed
                if sub_event.registration_url or sub_reg_needed is True or str(sub_reg_needed).lower() == "true":
                    main_event.registration_needed = True
                    break

    db.commit()

    print("[pipeline] Updated main_events with sub_event_ids.")
