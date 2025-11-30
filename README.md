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



## 10. Repository Structure

Below is an overview of the current repository layout and the purpose of each directory.

```text
data-science-project/project
├─ backend/
│  ├─ services/
│  │   ├─ email_downloader.py     # IMAP logic to download emails (Gmail/ZDV support)
│  │   ├─ event_pipeline.py       # Full pipeline: download → extract → deduplicate → store
│  │   ├─ event_recognizer.py     # LLM-based event extraction from email text
│  │   ├─ event_duplicator.py     # Deduplication logic using LLM comparison
│  │   └─ __init__.py
│  │
│  ├─ app.py                      # (Planned) FastAPI backend entrypoint
│  ├─ Dockerfile                  # Backend Docker configuration
│  └─ requirements.txt            # Python dependencies
│
├─ frontend/
│  ├─ src/                        # Frontend source code (React/Vite)
│  ├─ index.html                  # Frontend HTML entrypoint
│  ├─ package.json                # Frontend dependencies
│  ├─ vite.config.ts              # Vite configuration
│  ├─ tsconfig.json               # Typescript config
│  ├─ Dockerfile                  # Frontend Docker setup
│  └─ README.md                   # Frontend-specific documentation
│
├─ docker-compose.yml             # Combined backend/frontend container setup
├─ .gitignore
└─ README.md                      # Main project documentation (this file)







