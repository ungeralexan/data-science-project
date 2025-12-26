# Email Extraction Pipeline (IMAP → LLM → DB)

← [Back to README](../README.md)

This document explains how tuevent turns university mailing-list emails into structured events that are stored in the database and displayed in the frontend. It focuses on the extraction pipeline (ingestion, LLM contract, validation, deduplication, and main/sub-event handling).

Relevant backend files:
- `project/backend/services/email_downloader.py`
- `project/backend/services/event_recognizer.py`
- `project/backend/services/event_cleaner.py`
- `project/backend/services/event_duplicator.py`
- `project/backend/services/event_pipeline.py`

---


### What we consider an “event”
An event is a scheduled occurrence (e.g., talk, lecture, workshop, training, career event) that has at least an implied date/time and can be represented as a calendar entry.

### What we explicitly exclude
We do **not** treat these as events:
- invitations to participate in a study or survey
- general announcements without a scheduled occurrence
- administrative messages without an event-like structure

This classification is enforced primarily through the extraction prompt in `event_recognizer.py`.

---

## 2. Inputs: how emails enter the pipeline (`email_downloader.py`)

### 2.1 IMAP connection and selection
- The downloader connects to the configured university IMAP server (`IMAP_HOST`, `IMAP_PORT`) using SSL.
- It selects the `Inbox` and fetches the latest `limit` messages (default configured in `event_pipeline.py`).

### 2.2 Body extraction (plain text preferred, HTML as fallback)
For each email:
1. Prefer `text/plain` (non-attachment parts in multipart emails)
2. If no plain text exists, fall back to `text/html` and convert HTML → text via BeautifulSoup
3. If neither exists, use a placeholder (`[no text body]`)

### 2.3 Filtering: only “Rundmail” / “WiWiNews”
To reduce noise, an email is only included if the *body text* contains one of:
- `rundmail` (case-insensitive), or
- `wiwinews` (case-insensitive)

Only filtered-in emails are written to the extraction input file.

### 2.4 URL enrichment (additional context for the extractor)
Many emails contain links to event pages that carry missing details (exact dates/times, registration links, etc.). We therefore:
- extract URLs from the email text via regex (`https?://...`)
- fetch content for up to **3 URLs per email** (`MAX_URLS_PER_EMAIL = 3`)
- skip common non-event URLs (unsubscribe links, social media, maps, PDFs/images, ILIAS, etc.)
- extract readable text from HTML (remove script/style/nav/header/footer)
- cap fetched content at **10,000 characters per URL**

Fetched content is appended to the email body as a block:

`--- URL CONTENT FROM THIS EMAIL ---`

The extractor prompt is explicitly instructed to use this URL content to fill missing fields.

### 2.5 Output format: `all_emails.txt`
The downloader writes a single concatenated file:

`EMAIL_TEMP_DIR/all_emails.txt`


This file is the sole input to the LLM extraction step.

---

## 3. Extraction output contract (JSON schema) (`event_recognizer.py`)

### 3.1 Contract overview
The extractor returns a **JSON array** of event objects. Each object must contain the same set of keys, even if values are `null` (except for required non-null keys described below).

Important properties of the contract:
- output must be **valid JSON**
- output must be an **array** (`[]`)
- each element must match the schema
- no additional keys are allowed

### 3.2 Event object schema (field list)
Each extracted event includes:

**Core fields**
- `Title` (string or null)
- `Description` (string or null)

**Date/time fields**
- `Start_Date` (string or null)
- `End_Date` (string or null)
- `Start_Time` (string or null)
- `End_Time` (string or null)

**Location fields**
- `Location` (string or null)
- `Street` (string or null)
- `House_Number` (string or null)
- `Zip_Code` (string or null)
- `City` (string or null)
- `Country` (string or null)
- `Room` (string or null)
- `Floor` (string or null)

**Metadata**
- `Speaker` (string or null)
- `Organizer` (string or null)
- `Registration_Needed` (boolean or null)
- `URL` (string or null)
- `Image_Key` (string or null)

**Event grouping fields (required, non-null)**
- `Event_Type` (string, required): must be `"main_event"` or `"sub_event"`
- `Main_Event_Temp_Key` (string, required): temporary identifier used to link sub-events to their parent event

### 3.3 Main events vs sub-events (linking rule)
We represent multi-event announcements (lecture series, conferences, multi-session workshops) using:
- one `"main_event"` representing the parent/series
- multiple `"sub_event"` items representing individual sessions

Linking requirement:
- the parent and all sub-events share the same `Main_Event_Temp_Key`

Constraint enforced in prompting:
- “There cannot be a sub event without a main event.”

### 3.4 Example (typical output shape)
Example structure (simplified for readability):

```json
[
  {
    "Title": "Lecture Series: AI in Economics",
    "Start_Date": "01/10/2026",
    "End_Date": "02/21/2026",
    "Start_Time": null,
    "End_Time": null,
    "Description": "A weekly lecture series covering applications of AI in economics...",
    "Location": "University of Tübingen, Neue Aula",
    "Street": null,
    "House_Number": null,
    "Zip_Code": null,
    "City": "Tübingen",
    "Country": "Germany",
    "Room": null,
    "Floor": null,
    "Speaker": null,
    "Organizer": "WiWi Faculty",
    "Registration_Needed": null,
    "URL": "https://example.org/series",
    "Image_Key": "lecture",
    "Event_Type": "main_event",
    "Main_Event_Temp_Key": "ai_econ_series"
  },
  {
    "Title": "Session 1: Forecasting with Transformers",
    "Start_Date": "01/10/2026",
    "End_Date": "01/10/2026",
    "Start_Time": "06:15 PM",
    "End_Time": "07:45 PM",
    "Description": "Talk on transformer-based forecasting models and limitations...",
    "Location": "University of Tübingen, Neue Aula, Room 101",
    "Street": null,
    "House_Number": null,
    "Zip_Code": null,
    "City": "Tübingen",
    "Country": "Germany",
    "Room": "101",
    "Floor": null,
    "Speaker": "Dr. X",
    "Organizer": "WiWi Faculty",
    "Registration_Needed": false,
    "URL": "https://example.org/session1",
    "Image_Key": "lecture",
    "Event_Type": "sub_event",
    "Main_Event_Temp_Key": "ai_econ_series"
  }
]
``

---

## 4. Prompt strategy (Gemini extraction) (`event_recognizer.py`)

The extractor is driven by a system prompt designed for university mailing-list emails (German/English). It is written to handle three cases:

- emails describing **one** event,
- emails describing **multiple** events (series / sessions),
- emails that contain **no** real event.

The prompt is strict about formatting and output shape, because the result is consumed directly by later pipeline stages (filtering, deduplication, DB insertion).

### 4.1 Language and formatting

- Translate non-English text into English **except** proper names (institutions, building names, street names, person names).
- Normalize formats:
  - Date requested as `MM/DD/YYYY`
  - Time requested as `HH:MM AM/PM`
- Interpret German academic time markers:
  - `s.t.` = starts exactly on the hour
  - `c.t.` = starts 15 minutes after the hour  
    (and the prompt also instructs the model to treat `c.t.` end times as “15 minutes before the hour” when an end time is expressed in that style)

### 4.2 Using URL content as additional context

If an email contains the block:

`--- URL CONTENT FROM THIS EMAIL ---`

the model is instructed to:
- use it to fill missing event details (dates, times, speakers, registration requirements, location),
- prefer URL content over the email body if it is more specific (e.g., an agenda page contains exact times while the email is vague).

This URL block is produced upstream by `email_downloader.py` and is embedded directly under the corresponding email body in the extraction input.

### 4.3 Title and description quality requirements

The prompt aims for calendar-ready output:

- Titles must be short and “calendar-like” (no long sentences, no full email headlines with many clauses).
- If no explicit title exists, the model should generate a concise 4–6 word title.
- Descriptions must be written as event descriptions for end users:
  - no references to the email itself
  - focus on what happens, who it is for, and what participants gain
- `Registration_Needed` should only be set to `true` or `false` if the email or URL content explicitly states it; otherwise it must be `null`.

### 4.4 Output constraints

The model must return:
- **JSON only** (no markdown fences, no explanation text),
- a **JSON array** of event objects,
- **no keys beyond the schema** enforced by `response_schema`.

If there is no clear event in a given email, the model should return nothing for that email (i.e., it should not invent events).

---

## 5. Validation and normalization (post-extraction)

LLM output is not inserted directly. We apply deterministic filtering and database maintenance to keep the event feed clean and consistent.

### 5.1 Filtering out past events (`event_cleaner.py`)

We keep events that are today or in the future. The logic is sub-event aware:

**Main event without sub-events**
- Keep only if `End_Date` (or `Start_Date` if end date is missing) is today or future.

**Main event with sub-events**
- Keep the main event if **any** of its sub-events is in the future.
- If kept, keep **all** of its sub-events (including past ones) so the series remains coherent in the UI.

**Orphan sub-events**
- Sub-events that do not match any main event key are treated separately and kept only if they are future events.

**Date parsing**
- The cleaner attempts multiple formats (e.g., `YYYY-MM-DD`, `DD.MM.YYYY`, `January 15, 2025`).
- If parsing fails, we keep the event (fail-open). The goal is to avoid dropping a valid future event due to formatting differences.

### 5.2 Archiving past events in the database (`event_cleaner.py`)

Before processing new emails, the pipeline archives old DB entries by setting `archived_event=True`.

Rules:
- Main events without sub-events: archive if end/start date is in the past.
- Main events with sub-events: archive only if **all** sub-events are in the past.
- Orphan sub-events: archive if in the past.

This reduces feed clutter without deleting history.

---

## 6. Deduplication (LLM-based) (`event_duplicator.py`)

After filtering, we deduplicate candidates against events already stored in the database.

### 6.1 Why LLM-based deduplication

Announcements are often repeated with minor wording changes (forwards, reminders, reposts). A strict string match would miss duplicates frequently. We therefore use an LLM to make a semantic duplicate decision based on:

- title similarity,
- date/time overlap,
- location similarity,
- description similarity.

### 6.2 Batch decision contract

Deduplication runs in batch and returns one decision per candidate event in the same order:

```json
[
  {"is_new": true},
  {"is_new": false}
]


### Deduplication contract enforcement (response schema)

Deduplication decisions are constrained by a strict response schema (`BATCH_SCHEMA`). If the model violates the schema or the response cannot be parsed as valid JSON, we **fail open** and keep the candidate events (i.e., treat them as new) to avoid accidentally dropping valid events.

### 6.3 Data passed to the LLM

**Candidates**
- Full extracted event dictionaries produced by the extractor (`event_recognizer.py`).

**Existing DB events**
- A simplified summary per stored event:
  - `id`
  - `Title`
  - `Start_Date` / `End_Date`
  - `Location`
  - `Description` (truncated to 500 characters)

**Separate runs**
- Deduplication is executed separately for:
  - main events (`filter_new_main_events`)
  - sub-events (`filter_new_sub_events`)

**Fallback behavior**
- If the LLM response cannot be parsed or the output length does not match the candidate list length, the code defaults to treating all candidates as new (**fail-open**).

---

## 7. Database insertion and linking (`event_pipeline.py`)

### 7.1 Insert order

We insert events in this order because sub-events require a database `main_event_id`:

1. Insert new main events  
2. Insert new sub-events  
3. Update `sub_event_ids` on each main event  

### 7.2 Linking strategy: `Main_Event_Temp_Key`

Linking happens in two steps:

- While inserting main events, the pipeline builds a mapping:  
  `Main_Event_Temp_Key → main_event.id`

- While inserting sub-events, each sub-event uses its `Main_Event_Temp_Key` to look up and set `main_event_id`.

In addition, the pipeline collects sub-event IDs per main event and writes them back into `MainEventORM.sub_event_ids` (JSON column) so the frontend can load sub-events efficiently.

### 7.3 Missing end date handling

At insert time, if `End_Date` is missing, the pipeline sets:

- `End_Date = Start_Date`

This avoids incomplete date ranges in the database and simplifies downstream logic (filtering and UI display).

---

## 8. Current constraints and known issues

### 8.1 Multi-day “list” instruction vs schema

The extraction prompt contains a note suggesting that multi-day dates/times could be stored “in a list.” However, the enforced schema defines:

- `Start_Date`, `End_Date`, `Start_Time`, `End_Time` as strings (nullable), not arrays.

In practice, multi-day events are represented via:
- `Start_Date` + `End_Date` as strings (and optionally time ranges).

### 8.2 Email filtering is keyword-based

Only emails containing `"rundmail"` or `"wiwinews"` in the body are processed. This is simple and effective but may exclude relevant event emails from other formats or mailing lists.

### 8.3 URL fetching is capped and skips certain formats

URL enrichment:
- fetches up to 3 URLs per email,
- skips PDFs/images and known non-event domains.

Event details that exist only in skipped content (e.g., PDF flyers) will not be added as extraction context.

---

## 9. Pipeline entrypoint

The full end-to-end pipeline (archive → download → extract → filter → dedup → insert) is executed by:

- `run_email_to_db_pipeline(...)` in `event_pipeline.py`

This is the function scheduled by the backend to run periodically (as described in the README).
