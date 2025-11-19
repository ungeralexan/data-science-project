from typing import List
import pandas as pd

from sqlalchemy.orm import Session

from data.database.database_events import SessionLocal, EventORM

from services.email_downloader import download_latest_emails 
from services.event_duplicator import is_duplicate_event
from services.event_recognizer import extract_event_info_with_llm

def run_email_to_db_pipeline(limit: int = 10, outdir: str = "data/temp_emails") -> None:
    """
    Runs the pipeline to download emails, extract events, and insert them into the database.
    """

    #1) Downloads latest emails
    print("[run_email_to_db_pipeline] Downloading latest emails...")
    download_latest_emails(limit=limit)

    # 2) Reads combined text
    from pathlib import Path

    all_emails_path = Path(outdir) / "all_emails.txt"
    if not all_emails_path.exists():
        print("[run_email_to_db_pipeline] No combined email file created.")
        return

    combined_text = all_emails_path.read_text(encoding="utf-8")

    # 3) Extracts events via LLM
    events_raw = extract_event_info_with_llm(combined_text)
    print(f"[run_email_to_db_pipeline] LLM returned {len(events_raw)} events.")

    # 4) Opens DB session and insert non-duplicates
    with SessionLocal() as db:
        insert_non_duplicate_events(db, events_raw)

    # 5) Convert to DataFrame
    df_results = pd.DataFrame(events_raw)

    # 6) Save to XLSX (one row per event)
    out_path = Path("data/temp_emails/extracted_event_info.xlsx")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    df_results.to_excel(out_path, index=False)

    print(f"Saved {len(df_results)} events to {out_path}")

def insert_non_duplicate_events(db: Session, events_raw: List[dict]) -> None:
    """
    Inserts events into DB, skipping duplicates as determined by LLM.
    """
    # Fetch existing events once
    existing_events = db.query(EventORM).all()
    inserted_count = 0

    for event in events_raw:
        title = event.get("Title")
        
        if not title:
            # Skip events without any title
            continue

        # Ask LLM if this candidate is a duplicate
        if is_duplicate_event(event, existing_events):
            print(f"[pipeline] Skipping duplicate event: {title}")
            continue

        # Map LLM fields → DB columns
        start_date_str = event.get("Start_Date") or ""
        end_date_str = event.get("End_Date") or start_date_str

        new_row = EventORM(
            title = title,
            start_date = event.get("Start_Date"),
            end_date=end_date_str,
            start_time = event.get("Start_Time"),
            end_time = event.get("End_Time"),
            description = event.get("Description"),
            location=event.get("Location") or "",
            speaker=event.get("Speaker"),
            organizer=event.get("Organizer"),
            registration_needed=event.get("Registration_Needed"),
            url=event.get("URL"),
            image_key=None
        )
        
        db.add(new_row)
        db.flush()  # assign new_row.id without committing yet

        # Add newly inserted event to in-memory list so future candidates see it
        existing_events.append(new_row)
        inserted_count += 1

    db.commit()
    print(f"[run_email_to_db_pipeline] Inserted {inserted_count} new events into DB.")
