"""
Export LLM-extracted events to CSV for manual evaluation.

Usage (from project/backend):

    python -m tests.export_llm_events [--limit 20]

This will:
  1) download the latest N emails into data/temp_emails/all_emails.txt
  2) run extract_event_info_with_llm on them
  3) save the events to data/eval_events/llm_events_<timestamp>.csv
"""

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import argparse
import csv

from config import EMAIL_TEMP_DIR, EMAIL_PIPELINE_DEFAULT_LIMIT  # type: ignore
from services.email_downloader import download_latest_emails  # type: ignore
from services.event_recognizer import extract_event_info_with_llm  # type: ignore


EVAL_DIR = Path("data") / "eval_events"


def load_all_emails_text(limit: int) -> str:
    print(f"[eval] Downloading latest {limit} emails (Rundmail / WiWiNews only)...")
    download_latest_emails(limit=limit)

    all_emails_path = Path(EMAIL_TEMP_DIR) / "all_emails.txt"

    if not all_emails_path.exists():
        raise FileNotFoundError(
            f"[eval] Combined email file not found at {all_emails_path}. "
            "Did download_latest_emails run successfully?"
        )

    print(f"[eval] Using combined email file: {all_emails_path}")
    return all_emails_path.read_text(encoding="utf-8")


def save_events_to_csv(events: List[Dict[str, Any]]) -> Path:
    """Save events to a timestamped CSV that you can open in Excel."""
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = EVAL_DIR / f"llm_events_{run_id}.csv"

    # Adjust this list to your event schema if needed
    fieldnames = [
        "run_id",
        "event_index",
        "Title",
        "Start_Date",
        "End_Date",
        "Start_Time",
        "End_Time",
        "Location",
        "Organizer",
        "Speaker",
        "Description",
        "Image_Key",  # or whatever you call the image / category field
    ]

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for idx, ev in enumerate(events, start=1):
            row = {
                "run_id": run_id,
                "event_index": idx,
            }
            for key in fieldnames[2:]:
                row[key] = ev.get(key, "")
            writer.writerow(row)

    print(f"[eval] Saved {len(events)} events to {csv_path}")
    return csv_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=EMAIL_PIPELINE_DEFAULT_LIMIT,
        help="How many latest emails to download.",
    )
    args = parser.parse_args()

    all_emails_text = load_all_emails_text(limit=args.limit)

    print("[eval] Calling extract_event_info_with_llm() ...")
    events = extract_event_info_with_llm(all_emails_text)

    if not isinstance(events, list):
        print("[eval] WARNING: extract_event_info_with_llm did not return a list.")
        return

    save_events_to_csv(events)


if __name__ == "__main__":
    main()
