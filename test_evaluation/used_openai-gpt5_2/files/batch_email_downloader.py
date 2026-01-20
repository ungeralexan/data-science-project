import os
import re
import json
import ssl
import hashlib
import imaplib
import email
from datetime import datetime
from email.policy import default
from typing import Dict, Any, Optional, List

import warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from backend.config import IMAP_HOST, IMAP_PORT  # pylint: disable=import-error


warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


# ----------------------------
# Helpers
# ----------------------------
def _safe_filename(s: str) -> str:
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
            "schema_version": "1.1",
            "created_at": datetime.utcnow().isoformat(),
            "dataset": {
                "target_count": None,
                "batch_count": None,
                "batch_size": None,
            },
            "emails": [],     # list of minimal metadata dicts
            "email_ids": [],  # convenience cache for idempotency
            "batches": {},    # batch_name -> list[email_id]
        }
    with open(index_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_index(index_path: str, index: Dict[str, Any]) -> None:
    index["updated_at"] = datetime.utcnow().isoformat()
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)


def _render_email_txt(subject: str, sender: str, date_str: str, body: str) -> str:
    return (
        f"Subject: {subject}\n"
        f"From: {sender}\n"
        f"Date: {date_str}\n\n"
        f"{body}\n"
    )


# ----------------------------
# Main downloader
# ----------------------------
def download_emails_batched(
    *,
    out_dir: str,
    # dataset shape
    target_count: int = 150,
    batch_count: int = 5,
    batch_size: int = 30,
    # IMAP fetch strategy
    fetch_chunk_size: int = 25,
    max_fetch_uids: Optional[int] = None,
    # files
    index_filename: str = "index.json",
    secrets_path: str = "secrets.json",
) -> Dict[str, Any]:
    """
    Download emails newest-first until `target_count` emails that pass the filter are stored.

    This function is:
    - Batched: fetches `fetch_chunk_size` emails per IMAP iteration
    - Idempotent: never duplicates already-stored emails (stable email_id)
    - Evaluation-ready: stores per-email JSON, per-email TXT, per-batch combined TXT, and index.json

    Batch partitioning:
    - After download, emails are assigned to batches: batch_01 ... batch_0N
    - Each batch contains exactly `batch_size` emails
    - Requires: target_count == batch_count * batch_size
    """
    if target_count != batch_count * batch_size:
        raise ValueError(
            f"Invalid dataset shape: target_count ({target_count}) must equal "
            f"batch_count ({batch_count}) * batch_size ({batch_size})."
        )

    os.makedirs(out_dir, exist_ok=True)

    emails_json_dir = os.path.join(out_dir, "emails_json")
    emails_txt_dir = os.path.join(out_dir, "emails_txt")
    batches_dir = os.path.join(out_dir, "batches")

    os.makedirs(emails_json_dir, exist_ok=True)
    os.makedirs(emails_txt_dir, exist_ok=True)
    os.makedirs(batches_dir, exist_ok=True)

    index_path = os.path.join(out_dir, index_filename)

    # Load credentials
    with open(secrets_path, "r", encoding="utf-8") as f:
        secrets = json.load(f)
    user = secrets["USER_ZDV"]
    password = secrets["USER_PASSWORD"]

    # Load existing index (idempotency)
    index = _load_index(index_path)
    existing_ids = set(index.get("email_ids", []))

    # Store dataset params in index (for auditability)
    index["dataset"] = {
        "target_count": target_count,
        "batch_count": batch_count,
        "batch_size": batch_size,
        "fetch_chunk_size": fetch_chunk_size,
        "filter": "body contains 'rundmail' or 'wiwinews'",
    }

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
            chunk_uids = uids_newest_first[cursor : cursor + fetch_chunk_size]
            cursor += fetch_chunk_size

            for uid in chunk_uids:
                # Fetch raw email
                typ, msg_data = M.fetch(uid, "(RFC822)")  # pylint: disable=unused-variable
                raw = msg_data[0][1]
                em = email.message_from_bytes(raw, policy=default)

                subject = em.get("subject") or ""
                sender = em.get("from") or ""
                date_str = em.get("date") or ""
                message_id = (em.get("message-id") or "").strip()

                body = _extract_text_from_email(em)

                # Apply filter
                if not _passes_filter(body):
                    continue

                # Stable email_id
                if message_id:
                    email_id = _safe_filename(message_id.strip("<>"))
                else:
                    snippet = body[:200]
                    email_id = _hash_fallback(sender, subject, date_str, snippet)

                # Idempotency: skip if already stored
                if email_id in existing_ids:
                    continue

                # Build record
                email_record: Dict[str, Any] = {
                    "schema_version": "1.1",
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

                # Write per-email JSON (never overwrite)
                json_path = os.path.join(emails_json_dir, f"{email_id}.json")
                if not os.path.exists(json_path):
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(email_record, f, ensure_ascii=False, indent=2)

                # Write per-email TXT (never overwrite)
                txt_path = os.path.join(emails_txt_dir, f"{email_id}.txt")
                if not os.path.exists(txt_path):
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(_render_email_txt(subject, sender, date_str, body))

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

                if len(existing_ids) >= target_count:
                    break

    finally:
        M.logout()

    # Persist index caches
    index["email_ids"] = sorted(list(existing_ids))

    # Deterministic batching: use index["email_ids"] order (stable)
    # Note: if you want "newest-first" batching, replace with a sort based on email metadata.
    sorted_ids: List[str] = list(index["email_ids"])

    batches: Dict[str, List[str]] = {}
    for b in range(batch_count):
        batch_name = f"batch_{b+1:02d}"
        start = b * batch_size
        end = start + batch_size
        batches[batch_name] = sorted_ids[start:end]

    index["batches"] = batches

    # Write combined batch TXT files (overwrites allowed, because it is derived output)
    for batch_name, email_ids in batches.items():
        combined_path = os.path.join(batches_dir, f"{batch_name}.txt")
        with open(combined_path, "w", encoding="utf-8") as out_f:
            out_f.write(f"=== {batch_name} ({len(email_ids)} emails) ===\n\n")
            for i, eid in enumerate(email_ids, start=1):
                per_email_txt = os.path.join(emails_txt_dir, f"{eid}.txt")
                out_f.write(f"\n\n---------------- EMAIL {i:03d} / {eid} START ----------------\n")
                if os.path.exists(per_email_txt):
                    out_f.write(open(per_email_txt, "r", encoding="utf-8").read())
                else:
                    out_f.write("[missing per-email txt]\n")
                out_f.write(f"---------------- EMAIL {i:03d} / {eid} END ----------------\n")

    _save_index(index_path, index)

    kept_count_after = len(existing_ids)
    print(
        f"[batch_email_downloader] Stored {kept_count_after - kept_count_before} new emails. "
        f"Total kept emails in dataset: {kept_count_after} (target={target_count}).\n"
        f"[batch_email_downloader] Output folder: {out_dir}\n"
        f"[batch_email_downloader] Batches written to: {batches_dir}"
    )

    return index
