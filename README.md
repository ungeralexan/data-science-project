# Tübingen Event Planner — Data Science Project
Data Science Project repository for the Tübingen event planner.  
**Team:** Veja, Maurice, Alex

---
##  Project Goal
Turn unstructured university mailing-list messages into a **centralized, personalized event feed**, so students no longer miss:
- talks
- workshops
- deadlines
- student group events
- department announcements

All events will be extracted automatically and displayed in a clean frontend UI.

---

##  Email Ingestion (current architecture)
We use a **central project Gmail inbox** as the single source of truth for all event-related mails.

- Personal uni accounts forward all incoming mails to the project Gmail.
- The backend connects to Gmail via **IMAP (read-only)**.
- A Python script (`email_downloader.py`) downloads the latest emails and:
  - converts HTML to plain text (via BeautifulSoup)
  - filters for likely Rundmails (e.g. keywords like *rundmail*, *wiwinews*)
  - writes a concatenated `all_emails.txt` file for further processing



--- 








