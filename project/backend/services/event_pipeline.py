from typing import List
import pandas as pd
from pathlib import Path

from sqlalchemy.orm import Session

from data.database.database_events import SessionLocal, EventORM  # pylint: disable=import-error

from services.email_downloader import download_latest_emails   # pylint: disable=import-error
from services.event_duplicator import filter_new_events  # pylint: disable=import-error
from services.event_recognizer import extract_event_info_with_llm  # pylint: disable=import-error

def run_email_to_db_pipeline(limit: int = 15, outdir: str = "data/temp_emails") -> None:
    """
    Runs the pipeline to download emails, extract events, and insert them into the database.
    """

    #1) Downloads latest emails
    print("[pipeline] Downloading latest emails...")
    download_latest_emails(limit=limit)

    # 2) Reads combined text file
    all_emails_path = Path(outdir) / "all_emails.txt"

    if not all_emails_path.exists():
        print("[pipeline] No combined email file created.")
        return

    combined_text = all_emails_path.read_text(encoding="utf-8")

    # 3) Extracts events via LLM
    try:
        print("[extract_event_info_with_llm] Extracting events via LLM...")
        events_raw = extract_event_info_with_llm(combined_text)
        print(f"[extract_event_info_with_llm] LLM returned {len(events_raw)} events.")
    except Exception as e: # pylint: disable=broad-except
        print(f"[extract_event_info_with_llm] Error during event extraction: {e}")
        return

    # 4) Opens DB session and insert non-duplicates
    with SessionLocal() as db:
        insert_non_duplicate_events(db, events_raw)

    # 5) Convert all extracted events (not only new ones) to DataFrame and save
    # This is temporary for analysis purposes
    df_results = pd.DataFrame(events_raw)
    out_path = Path(outdir) / "extracted_event_info.xlsx"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_results.to_excel(out_path, index=False)

    print(f"Saved {len(df_results)} events to {out_path}")


def insert_non_duplicate_events(db: Session, events_raw: List[dict]) -> None:
    """
    Inserts events into DB, skipping duplicates based on a *single* batch LLM call.
    """

    # Exit if no events to insert
    if not events_raw:
        print("[insert_non_duplicate_events] No events to insert.")
        return

    # Fetch existing events once from DB
    existing_events = db.query(EventORM).all()

    # 1) Ask LLM which candidates are new in one batch
    try:
        new_events_raw = filter_new_events(events_raw, existing_events)
    except Exception as e: # pylint: disable=broad-except
        print(f"[insert_non_duplicate_events] Error in batch dedup: {e}")
        # Fallback: treat all as new (or none if you're conservative)
        new_events_raw = events_raw

    print(f"[insert_non_duplicate_events] {len(new_events_raw)} events considered new by LLM.")

    # 2) Insert only new events into DB
    inserted_count = 0

    # Insert new events into DB
    for event in new_events_raw:

        title = event.get("Title")
        if not title:
            # Skip events without any title
            continue

        # Handle missing end date by using start date
        start_date_str = event.get("Start_Date") or ""
        end_date_str = event.get("End_Date") or start_date_str

        # Create new EventORM row
        new_row = EventORM(
            title = title,
            start_date = start_date_str,
            end_date = end_date_str,
            start_time = event.get("Start_Time"),
            end_time = event.get("End_Time"),
            description = event.get("Description"),
            location = event.get("Location") or "",
            speaker = event.get("Speaker"),
            organizer = event.get("Organizer"),
            registration_needed = event.get("Registration_Needed"),
            url = event.get("URL"),
            image_key = None,
        )

        # Add new row to session
        db.add(new_row)

        # Increment counter
        inserted_count += 1

    # Commit all new rows at once
    db.commit()
    print(f"[run_email_to_db_pipeline] Inserted {inserted_count} new events into DB.")
