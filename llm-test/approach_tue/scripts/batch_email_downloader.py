import os
import re
import json
import ssl
import hashlib
import imaplib
import email
from datetime import datetime
from email.policy import default
from typing import Dict, Any, List, Optional, Tuple

import warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from config import IMAP_HOST, IMAP_PORT  # pylint: disable=import-error

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def _safe_filename(s: str) -> str:
    # Keep filenames simple and stable
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", s).strip("_")


def _hash_fallback(sender: str, subject: str, date_str: str, body_snippet: str) -> str:
    raw = f"{sender}|{subject}|{date_str}|{body_snippet}".encode("utf-8", errors="ignore")
    return hashlib.sha256(raw).hexdigest()[:32]


def _extract_text_from_email(em: email.message.EmailMessage) -> str:
    text: Optional[str] = None

    if em.is_multipart():
        for part in em.walk():
            if part.get_content_type() == "text/plain" and not part.get_content_disposition():
                text = part.get_content()
                break
    else:
        if em.get_content_type() == "text/plain":
            text = em.get_content()

    if text is None:
        for part in em.walk():
            if part.get_content_type() == "text/html":
                html = part.get_content()
                text = BeautifulSoup(html, "lxml").get_text("\n")
                break

    return text or "[no text body]"


def _passes_filter(body: str) -> bool:
    b = body.lower()
    return ("rundmail" in b) or ("wiwinews" in b)


def _load_index(index_path: str) -> Dict[str, Any]:
    if not os.path.exists(index_path):
        return {
            "schema_version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "emails": [],  # list of minimal metadata dicts
            "email_ids": [],  # convenience cache
        }
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_index(index_path: str, index: Dict[str, Any]) -> None:
    index["updated_at"] = datetime.utcnow().isoformat()
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def download_emails_batched(
    *,
    out_dir: str,
    index_filename: str = "index.json",
    target_count: int = 105,
    batch_size: int = 25,
    max_fetch_uids: Optional[int] = None,
    secrets_path: str = "secrets.json",
) -> Dict[str, Any]:
    """
    Download emails newest-first in repeated batches until `target_count` emails that pass the filter are stored.

    - Batched: fetches `batch_size` messages per iteration.
    - Idempotent: skips emails already in index (by stable email_id).
    - Storage: one JSON per email + a dataset index.

    Returns the updated index dict.
    """
    os.makedirs(out_dir, exist_ok=True)
    emails_dir = os.path.join(out_dir, "emails")
    os.makedirs(emails_dir, exist_ok=True)
    index_path = os.path.join(out_dir, index_filename)

    # Load credentials
    with open(secrets_path, "r", encoding="utf-8") as f:
        secrets = json.load(f)

    user = secrets["USER_ZDV"]
    password = secrets["USER_PASSWORD"]

    # Load existing index (idempotency)
    index = _load_index(index_path)
    existing_ids = set(index.get("email_ids", []))

    # Connect
    context = ssl.create_default_context()
    M = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=context)
    M.login(user, password)
    M.select("Inbox")

    # Get all UIDs
    typ, data = M.search(None, "ALL")  # pylint: disable=unused-variable
    all_uids = data[0].split()

    # Iterate newest-first
    uids_newest_first = list(reversed(all_uids))
    if max_fetch_uids is not None:
        uids_newest_first = uids_newest_first[:max_fetch_uids]

    kept_count_before = len(existing_ids)
    cursor = 0

    try:
        while len(existing_ids) < target_count and cursor < len(uids_newest_first):
            batch_uids = uids_newest_first[cursor : cursor + batch_size]
            cursor += batch_size

            for uid in batch_uids:
                # Fetch
                typ, msg_data = M.fetch(uid, "(RFC822)")  # pylint: disable=unused-variable
                raw = msg_data[0][1]
                em = email.message_from_bytes(raw, policy=default)

                subject = em.get("subject") or ""
                sender = em.get("from") or ""
                date_str = em.get("date") or ""
                message_id = (em.get("message-id") or "").strip()

                body = _extract_text_from_email(em)

                # Apply filter (keep consistent with baseline for now)
                if not _passes_filter(body):
                    continue

                # Build stable email_id
                if message_id:
                    email_id = _safe_filename(message_id.strip("<>"))
                else:
                    snippet = body[:200]
                    email_id = _hash_fallback(sender, subject, date_str, snippet)

                if email_id in existing_ids:
                    continue

                email_record: Dict[str, Any] = {
                    "schema_version": "1.0",
                    "email_id": email_id,
                    "message_id": message_id,
                    "imap_uid": uid.decode("utf-8", errors="ignore") if isinstance(uid, bytes) else str(uid),
                    "subject": subject,
                    "from": sender,
                    "date": date_str,
                    "body_text": body,
                    "filter_reason": "body contains 'rundmail' or 'wiwinews'",
                    "downloaded_at": datetime.utcnow().isoformat(),
                }

                # Write per-email JSON
                email_path = os.path.join(emails_dir, f"{email_id}.json")
                with open(email_path, "w", encoding="utf-8") as f:
                    json.dump(email_record, f, ensure_ascii=False, indent=2)

                # Update index
                index["emails"].append(
                    {
                        "email_id": email_id,
                        "subject": subject,
                        "from": sender,
                        "date": date_str,
                        "message_id": message_id,
                    }
                )
                existing_ids.add(email_id)

                # Early stop if reached target
                if len(existing_ids) >= target_count:
                    break

    finally:
        M.logout()

    # Persist index caches
    index["email_ids"] = sorted(list(existing_ids))
    _save_index(index_path, index)

    kept_count_after = len(existing_ids)
    print(
        f"[batch_email_downloader] Stored {kept_count_after - kept_count_before} new emails. "
        f"Total kept emails in dataset: {kept_count_after} (target={target_count})."
    )

    return index
