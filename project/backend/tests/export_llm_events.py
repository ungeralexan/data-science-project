"""
Export LLM-extracted events directly to an Excel file (.xlsx) for evaluation.

Usage (from project/backend):

    python -m tests.export_llm_events_xlsx --limit 20
"""

from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import argparse

from openpyxl import Workbook
from openpyxl.utils import get_column_letter

from config import EMAIL_TEMP_DIR, EMAIL_PIPELINE_DEFAULT_LIMIT  # type: ignore
from services.email_downloader import download_latest_emails  # type: ignore
from services.event_recognizer import extract_event_info_with_llm  # type: ignore


EVAL_DIR = Path("data") / "eval_events"


def load_all_emails_text(limit: int) -> str:
    """Download and load the combined all_emails.txt."""
    print(f"[eval] Downloading latest {limit} emails...")
    download_latest_emails(limit=limit)

    all_emails_path = Path(EMAIL_TEMP_DIR) / "all_emails.txt"

    if not all_emails_path.exists():
        raise FileNotFoundError(
            f"[eval] Combined email file not found at {all_emails_path}"
        )

    print(f"[eval] Using: {all_emails_path}")
    return all_emails_path.read_text(encoding="utf-8")


def save_events_to_excel(events: List[Dict[str, Any]]) -> Path:
    """Save events into an Excel file for manual inspection."""
    EVAL_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    xlsx_path = EVAL_DIR / f"llm_events_{timestamp}.xlsx"

    wb = Workbook()
    ws = wb.active
    ws.title = "LLM Events"

    # Define structure
    headers = [
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
        "Image_Key",
    ]

    ws.append(headers)

    # Fill rows
    for idx, ev in enumerate(events, start=1):
        row = [
            idx,
            ev.get("Title", ""),
            ev.get("Start_Date", ""),
            ev.get("End_Date", ""),
            ev.get("Start_Time", ""),
            ev.get("End_Time", ""),
            ev.get("Location", ""),
            ev.get("Organizer", ""),
            ev.get("Speaker", ""),
            ev.get("Description", ""),
            ev.get("Image_Key", ""),  # whatever key you use for category
        ]
        ws.append(row)

    # Auto-size columns
    for col_idx, column_title in enumerate(headers, start=1):
        column_letter = get_column_letter(col_idx)
        ws.column_dimensions[column_letter].width = min(max(len(column_title), 20), 50)

    wb.save(xlsx_path)
    print(f"[eval] Excel file saved: {xlsx_path}")

    return xlsx_path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--limit",
        type=int,
        default=EMAIL_PIPELINE_DEFAULT_LIMIT,
        help="How many latest emails to fetch",
    )
    args = parser.parse_args()

    all_emails = load_all_emails_text(limit=args.limit)

    print("[eval] Running LLM extraction...")
    events = extract_event_info_with_llm(all_emails)

    if not isinstance(events, list):
        print("[eval] ERROR: LLM returned non-list structure")
        return

    save_events_to_excel(events)


if __name__ == "__main__":
    main()
