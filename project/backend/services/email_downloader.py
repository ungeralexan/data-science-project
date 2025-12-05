
import os
import json
from datetime import datetime
from typing import List

import imaplib
import email
import ssl
from email.policy import default
import warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from config import IMAP_HOST, IMAP_PORT, EMAIL_TEMP_DIR  # pylint: disable=import-error

#I disable this warning because it doesn't affect our use case
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# Create temp email directory if it doesn't exist
os.makedirs(EMAIL_TEMP_DIR, exist_ok=True)

# Load credentials from secrets.json
with open("secrets.json", "r", encoding="utf-8") as f:
    secrets = json.load(f)

USER = secrets["USER_ZDV"]       # ZDV Login
PASSWORD = secrets["USER_PASSWORD"]  # ZDV password

# -------- Email download function --------
def download_latest_emails(limit: int = 10) -> None:
    """
    Download the latest `limit` emails, save each as a separate .txt file,
    and also return ONE big string with all emails concatenated.
    """

    # ---- connect and login ----
    context = ssl.create_default_context()
    M = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT, ssl_context=context) # connect to server
    M.login(USER, PASSWORD)
    M.select("Inbox") # select inbox

    # ---- search and fetch emails ----
    # get all email UIDs.
    typ, data = M.search(None, "ALL")  # pylint: disable=unused-variable
    all_uids = data[0].split() # list of all email UIDs
    uids = all_uids[-limit:] # get the latest `limit` UIDs

    combined_chunks: List[str] = [] # List of email text blocks

    # ---- process each email ----
    for i, uid in enumerate(uids, 1):

        # ---- fetch email ----
        # RFC822 gets the full raw email text
        typ, msg_data = M.fetch(uid, "(RFC822)")  # pylint: disable=unused-variable
        raw = msg_data[0][1] #[0] is the tuple, [1] is the raw email bytes
        em = email.message_from_bytes(raw, policy=default) # parse email

        # ---- extract plain text body ----
        text = None

        # try to get plain text part directly. Multipart emails have multiple sections including attachments
        if em.is_multipart():
            for part in em.walk():
                # look for plain text parts without a content disposition. Content disposition is used for attachments
                if (
                    part.get_content_type() == "text/plain"
                    and not part.get_content_disposition()
                ):
                    text = part.get_content()
                    break
        else:
            # try to get plain text part directly. Non-multipart emails have a single section
            if em.get_content_type() == "text/plain":
                text = em.get_content()

        # ---- if no plain text, try HTML ----
        if text is None:
            
            # try to get HTML part and convert to text
            for part in em.walk():
                if part.get_content_type() == "text/html":
                    html = part.get_content()

                    # BeautifulSoup is used to convert HTML to plain text. It is a library for parsing HTML.
                    text = BeautifulSoup(html, "lxml").get_text("\n")
                    break

        # ---- if still no text, use placeholder ----
        subject = em.get("subject") or ""
        sender = em.get("from") or ""
        body = text or "[no text body]"

        # ---- filter for "Rundmail" emails ----
        if ("rundmail" in body.lower()) or ("wiwinews" in body.lower()):
            # ---- save per-email .txt file ----
            per_email_path = os.path.join(EMAIL_TEMP_DIR, f"msg_{i:04d}.txt")

            # write to file including Subject and From headers for context
            with open(per_email_path, "w", encoding="utf-8") as per_email_file:
                per_email_file.write(f"Subject: {subject}\n")
                per_email_file.write(f"From: {sender}\n\n")
                per_email_file.write(body + "\n")

            # ---- prepare combined string for LLM to process ----
            email_block = (
                f"--------------- EMAIL: {i} Start ---------------\n"
                f"Subject: {subject}\n"
                f"From: {sender}\n\n"
                f"{body}\n"
                f"--------------- EMAIL: {i} End ---------------\n"
            )

            # Append this email block to the list
            combined_chunks.append(email_block)

    # ---- logout from the email server ----
    M.logout()

    # --- combine all email blocks into one string ----
    combined_string = "\n\n".join(combined_chunks)

    # ---- delete old email .txt files ----
    for fname in os.listdir(EMAIL_TEMP_DIR):
        if fname.lower().endswith(".txt"):
            try:
                os.remove(os.path.join(EMAIL_TEMP_DIR, fname))
            except OSError:
                pass

    # ---- save combined all_emails.txt file ----
    all_path = os.path.join(EMAIL_TEMP_DIR, "all_emails.txt")

    with open(all_path, "w", encoding="utf-8") as all_path_files:
        all_path_files.write(combined_string)

    # ---- print status ----
    print(
        f"[{datetime.now().isoformat(timespec='seconds')}] "
        f"Saved concatenated email file: {all_path}"
    )