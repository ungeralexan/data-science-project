
import os
import json
from datetime import datetime
from typing import List

import imaplib
import email
import ssl
from email.policy import default
from bs4 import BeautifulSoup


HOST = "mailserv.uni-tuebingen.de"

os.makedirs("data/temp_emails", exist_ok = True)
OUTDIR = "data/temp_emails"

with open("secrets.json", "r", encoding="utf-8") as f:
    secrets = json.load(f)

USER = secrets["USER_ZDV"]       # ZDV Login
PASSWORD = secrets["USER_PASSWORD"]  # ZDV password

def download_latest_emails(limit: int = 10) -> None:
    """
    Download the latest `limit` emails, save each as a separate .txt file,
    and also return ONE big string with all emails concatenated.
    """
    context = ssl.create_default_context()
    M = imaplib.IMAP4_SSL(HOST, 993, ssl_context=context)
    M.login(USER, PASSWORD)
    M.select("Inbox")

    # get latest `limit` UIDs
    typ, data = M.search(None, "ALL")
    all_uids = data[0].split()
    uids = all_uids[-limit:]

    combined_chunks: List[str] = []  # for the big concatenated string

    for i, uid in enumerate(uids, 1):
        typ, msg_data = M.fetch(uid, "(RFC822)")
        raw = msg_data[0][1]
        em = email.message_from_bytes(raw, policy=default)

        # ---- extract text body (same logic as before) ----
        text = None
        if em.is_multipart():
            for part in em.walk():
                if (
                    part.get_content_type() == "text/plain"
                    and not part.get_content_disposition()
                ):
                    text = part.get_content()
                    break
        else:
            if em.get_content_type() == "text/plain":
                text = em.get_content()

        if text is None:
            # try HTML -> plain text
            for part in em.walk():
                if part.get_content_type() == "text/html":
                    html = part.get_content()
                    text = BeautifulSoup(html, "lxml").get_text("\n")
                    break

        subject = em.get("subject") or ""
        sender = em.get("from") or ""
        body = text or "[no text body]"

        # ---- write individual file (optional, as before) ----
        per_email_path = os.path.join(OUTDIR, f"msg_{i:04d}.txt")
        with open(per_email_path, "w", encoding="utf-8") as f:
            f.write(f"Subject: {subject}\n")
            f.write(f"From: {sender}\n\n")
            f.write(body + "\n")

        # ---- build the big concatenated block ----
        email_block = (
            f"--------------- EMAIL: {i} Start ---------------\n"
            f"Subject: {subject}\n"
            f"From: {sender}\n\n"
            f"{body}\n"
            f"--------------- EMAIL: {i} End ---------------\n"
        )

        combined_chunks.append(email_block)

    M.logout()

    # join all email blocks with a blank line between them
    combined_string = "\n\n".join(combined_chunks)

    # ---- delete old email .txt files ----
    for fname in os.listdir(OUTDIR):
        if fname.lower().endswith(".txt"):
            try:
                os.remove(os.path.join(OUTDIR, fname))
            except OSError:
                # you could log this if you want
                pass

    # ---- write the new combined file ----
    all_path = os.path.join(OUTDIR, "all_emails.txt")
    with open(all_path, "w", encoding="utf-8") as f:
        f.write(combined_string)

    print(
        f"[{datetime.now().isoformat(timespec='seconds')}] "
        f"Saved concatenated email file: {all_path}"
    )