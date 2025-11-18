import imaplib
import email
import ssl
from email.policy import default
from bs4 import BeautifulSoup
import os
import json

os.makedirs("emails_out", exist_ok=True)
outdir = "emails_out"

with open("secrets.json", "r", encoding="utf-8") as f:
    secrets = json.load(f)

HOST = "mailserv.uni-tuebingen.de"
USER = secrets["USER_ZDV"]  # your ZDV loginID
PASSWORD = secrets["USER_PASSWORD"]  # your ZDV password

context = ssl.create_default_context()
M = imaplib.IMAP4_SSL(HOST, 993, ssl_context=context)
M.login(USER, PASSWORD)
M.select("Inbox")   # folder name

# fetch UIDs of all messages (or use search criteria)
typ, data = M.search(None, "ALL")
uids = data[0].split()[-50:]  # only last 10 messages/ change as needed

for i, uid in enumerate(uids, 1):
    typ, msg_data = M.fetch(uid, "(RFC822)")
    raw = msg_data[0][1]
    em = email.message_from_bytes(raw, policy=default)

    # get text/plain if exists, else extract text from html
    text = None
    if em.is_multipart():
        for part in em.walk():
            if part.get_content_type() == "text/plain" and not part.get_content_disposition():
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

    with open(os.path.join(outdir, f"msg_{i:04d}.txt"), "w", encoding="utf-8") as f:
        f.write("Subject: " + (em.get('subject') or "") + "\n")
        f.write("From: " + (em.get('from') or "") + "\n\n")
        f.write(text or "[no text body]\n")

M.logout()
print("Saved", len(uids), "messages")
