
from pathlib import Path
from typing import List, Dict, Any
from google import genai

from config import EMAIL_TEMP_DIR, EMAIL_PIPELINE_DEFAULT_LIMIT  # type: ignore
from services.email_downloader import download_latest_emails  # type: ignore
from services.event_recognizer import extract_event_info_with_llm  # type: ignore


def load_all_emails_text(limit: int) -> str:
    """Download latest emails and return the combined all_emails.txt content."""
    print(f"[preview] Downloading latest {limit} emails (Rundmail / WiWiNews only)...")
    download_latest_emails(limit=limit)

    all_emails_path = Path(EMAIL_TEMP_DIR) / "all_emails.txt"

    if not all_emails_path.exists():
        raise FileNotFoundError(
            f"[preview] Combined email file not found at {all_emails_path}. "
            "Did download_latest_emails run successfully?"
        )

    print(f"[preview] Using combined email file: {all_emails_path}")
    return all_emails_path.read_text(encoding="utf-8")


def pretty_print_events(events: List[Dict[str, Any]]) -> None:
    """Print a compact summary of each event."""
    if not events:
        print("[preview] LLM did not return any events.")
        return

    print(f"[preview] LLM returned {len(events)} event(s).\n")

    for idx, ev in enumerate(events, start=1):
        title = ev.get("Title") or "<no title>"
        start_date = ev.get("Start_Date") or "?"
        end_date = ev.get("End_Date") or "?"
        start_time = ev.get("Start_Time") or "?"
        end_time = ev.get("End_Time") or "?"
        location = ev.get("Location") or "?"
        organizer = ev.get("Organizer") or "?"
        speaker = ev.get("Speaker") or "?"

        print("=" * 80)
        print(f"Event #{idx}")
        print("-" * 80)
        print(f"Title     : {title}")
        print(f"Date      : {start_date}  ->  {end_date}")
        print(f"Time      : {start_time}  ->  {end_time}")
        print(f"Location  : {location}")
        print(f"Organizer : {organizer}")
        print(f"Speaker   : {speaker}")
        print("=" * 80)
        print()


def main() -> None:
    # you can change this to 5, 10, 20, ... as you like
    limit = EMAIL_PIPELINE_DEFAULT_LIMIT

    all_emails_text = load_all_emails_text(limit=limit)

    print("[preview] Calling extract_event_info_with_llm() ...")
    events = extract_event_info_with_llm(all_emails_text)

    # events should be a list[dict] according to your code
    if not isinstance(events, list):
        print("[preview] WARNING: extract_event_info_with_llm did not return a list.")
    else:
        pretty_print_events(events)


if __name__ == "__main__":
    main()


# python -m tests.preview_llm_events