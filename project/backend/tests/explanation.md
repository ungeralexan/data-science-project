# LLM Extraction Quality Evaluation (Offline Benchmark)


## 1. Purpose of this evaluation
This project extracts structured university events from unstructured mailing-list emails using an LLM (Gemini Flash). Because LLMs can produce:
incorrect fields (hallucinations / wrong dates, times, locations), and
incomplete records (missing information that is present in the email),
we run an offline benchmark to evaluate output quality in a reproducible way and to identify systematic weaknesses for prompt/model improvements.


## 2. Constraints and design choices
We had a limited number of LLM requests available for testing.
Therefore, we designed the evaluation to work with one extraction run (one LLM call) while still being auditable.
We did not modify the production pipeline (no changes in services/ or the DB pipeline). All evaluation tooling is contained in project/backend/tests.


## 3. What “quality” means in this benchmark
We evaluate the extracted event objects on two dimensions:


### Correctness
Each extracted field should be supported by the source email (or URL content attached to that email). Examples of correctness errors:
wrong date/time (misread format, wrong year),
wrong location (taken from another email or unrelated website section),
invented speaker/organizer.


### Completeness
If an email clearly provides details (date, time, location, registration, etc.), they should appear in the extracted event. Examples:
date missing despite being explicitly stated,
location missing although clearly listed,
registration status missing even though explicitly required.


## 4. Evaluation scripts (tests folder)
All scripts below are located under:
project/backend/tests/

### 4.1 Existing scripts (baseline)
preview_llm_events.py
Purpose: quick local preview of the LLM output (console summary).
Use case: sanity check during development.
export_llm_events.py
Purpose: export LLM output to JSON and Excel for manual inspection.
Output: raw combined email input + extracted events in JSON and optional Excel.

### 4.2 New scripts created for this benchmark (audit + matching)
Because we must audit “event → source email” mapping reliably (and we only run one LLM call), two additional scripts were created:
export_llm_events_audit.py

Purpose: perform a single extraction run that is auditable.

Key features:
downloads emails (same method as pipeline),
applies a deterministic heuristic prefilter to reduce non-event emails (no LLM calls here),
runs one LLM extraction call on the reduced set,
forces each event to contain:
Source_Email_Index (which email block it came from)
Evidence (short supporting quote/snippet from that same email block)
This makes later correctness checks feasible without manually guessing which email generated which event.
build_matched_eval_pack.py
Purpose: create a minimal evaluation package after extraction.

Key features:
reads llm_events_<timestamp>.json,
extracts only those email blocks actually referenced by Source_Email_Index,
exports a compact “matched” email set and an Excel workbook that is easy to review.


## 5. Output artifacts (what files are produced)
All evaluation artifacts are written to:
project/backend/tests/local_eval/
This directory is intended to be gitignored because it may contain private email content.
Typical files:
From export_llm_events_audit.py:
all_emails_raw_<timestamp>.txt
Full concatenated email input produced by the downloader.
all_emails_filtered_<timestamp>.txt
Prefiltered subset (heuristic “likely event” emails only) used as LLM input.
email_index_<timestamp>.json
Subject/From lookup for the filtered email blocks.
llm_events_<timestamp>.json
Extracted events including Source_Email_Index and Evidence.
llm_events_<timestamp>.xlsx
Human-readable overview of events and the filtered emails.
From build_matched_eval_pack.py:
<prefix>_matched_emails.txt
Only those email blocks that produced at least one event (based on Source_Email_Index).
<prefix>_matched_emails_index.json
Subject/From lookup for matched emails.
<prefix>_matched_eval.xlsx
Excel with two sheets:
Events: event table (one row per event)
MatchedEmails: only emails referenced by events (easy lookup)
<prefix>_report.json
Small summary of counts and whether any Source_Email_Index was missing from the email file.


## 6. Reproducible workflow used in this benchmark

### Step 1 — Run the auditable extraction once
From project/backend:
python -m tests.export_llm_events_audit --limit 150
Notes:
This runs the email download + prefilter + one LLM call.
It does not insert anything into the database and does not run deduplication/recommendations.

### Step 2 — Build the minimal matched evaluation pack (no LLM calls)
Identify the produced filenames under tests/local_eval/ (timestamped). Then run:
python -m tests.build_matched_eval_pack \
  --events-json tests/local_eval/llm_events_YYYYMMDD_HHMMSS.json \
  --emails-txt  tests/local_eval/all_emails_raw_YYYYMMDD_HHMMSS.txt \
  --out-prefix  matched_YYYYMMDD_HHMMSS
This produces a compact set that can be reviewed efficiently and shared internally (subject to privacy constraints).

## 7. How the manual/LLM quality check is performed (overview)
After generating the matched pack, each event can be verified by:
locating its Source_Email_Index,
opening the corresponding email block in MatchedEmails or matched_emails.txt,
checking whether:
Title/date/time/location/organizer/speaker/registration/URL match the email content,
any extracted info is missing although explicitly stated,
any extracted info is unsupported (hallucination).
Quantitative KPIs and systematic error categories are derived from these comparisons.


## 8. What this benchmark does NOT test
Database insertion logic, WebSocket delivery, frontend rendering.
Deduplication performance (services/event_duplicator.py) unless explicitly included in a separate benchmark.
Recommendation quality (services/event_recommender.py).
This benchmark focuses strictly on extraction correctness/completeness from emails to structured event objects.


## Appendix: Why Source_Email_Index and Evidence were added
Without provenance, a reviewer must guess which email created which event. That makes correctness auditing unreliable and slow.
By requiring:
Source_Email_Index (email block identifier), and
Evidence (supporting snippet),
we can audit each event deterministically and document the result in a way that is reviewable by non-developers.



# LLM Extraction Quality Evaluation (Offline Benchmark)

## Testing and evaluation (what we did)
To make the extraction quality testable and auditable under a limited LLM-call budget, we executed a **single-run offline benchmark** designed to (1) preserve the production pipeline behavior, (2) generate artifacts suitable for manual review, and (3) enable deterministic “event → source email” traceability.

### Goals of the testing step
- **Verify correctness**: every extracted field must be supported by the source email content (or linked content explicitly referenced by the email).
- **Verify completeness**: if key event details are present in the email, they should appear in the extracted event object.
- **Make auditing reproducible**: reviewers should be able to validate each event without guessing which email produced it.

### Key design choice: one LLM extraction call
Because LLM usage was limited, the benchmark was designed around:
- **One extraction run (one LLM call)** on a reduced set of emails.
- **Deterministic prefiltering** (no LLM) to remove clearly non-event emails while keeping the process auditable.
- **Strict provenance fields** added to every extracted event to support review.

---

## What was added for the benchmark (new test scripts)
All evaluation tooling is contained in `project/backend/tests/` and does **not** modify the production services or database pipeline.

### 1) `export_llm_events_audit.py` (auditable single-run extraction)
**Purpose:** run one extraction in a way that is easy to validate.

**What it does:**
1. Downloads emails using the same approach as the production pipeline.
2. Applies a deterministic heuristic prefilter to keep only “likely event” emails (no LLM here).
3. Runs **one** LLM extraction call on the filtered email blocks.
4. Ensures every extracted event includes:
   - `Source_Email_Index`: the index of the email block that produced the event
   - `Evidence`: a short snippet/quote from the same email block supporting the extraction

**Why this matters:** it prevents ambiguous provenance and makes correctness checks feasible without manual guessing.

### 2) `build_matched_eval_pack.py` (minimal matched review package)
**Purpose:** produce a compact evaluation bundle after extraction (no LLM calls).

**What it does:**
- Reads the generated `llm_events_<timestamp>.json`
- Collects only the email blocks referenced by `Source_Email_Index`
- Exports a small, review-friendly package (text + Excel) containing:
  - only emails that produced at least one event, and
  - the extracted events that reference them

---

## Artifacts produced (for review and traceability)
All outputs are written to:
`project/backend/tests/local_eval/`  
(This directory is intended to be gitignored due to potentially private email content.)

### From `export_llm_events_audit.py`
- `all_emails_raw_<timestamp>.txt`  
  Full concatenated email input produced by the downloader.
- `all_emails_filtered_<timestamp>.txt`  
  Prefiltered subset (heuristic “likely event” emails only) used as LLM input.
- `email_index_<timestamp>.json`  
  Subject/From lookup for the filtered email blocks.
- `llm_events_<timestamp>.json`  
  Extracted events including `Source_Email_Index` and `Evidence`.
- `llm_events_<timestamp>.xlsx`  
  Human-readable overview of events and filtered emails.

### From `build_matched_eval_pack.py`
- `<prefix>_matched_emails.txt`  
  Only email blocks that produced at least one event (based on `Source_Email_Index`).
- `<prefix>_matched_emails_index.json`  
  Subject/From lookup for matched emails.
- `<prefix>_matched_eval.xlsx` with two sheets:
  - `Events`: one row per extracted event
  - `MatchedEmails`: only emails referenced by events (easy lookup)
- `<prefix>_report.json`  
  Summary counts + checks (e.g., whether any referenced `Source_Email_Index` is missing).

---

## Reproducible workflow used in the benchmark

### Step 1 — Run the auditable extraction once
From `project/backend/`:
```bash
python -m tests.export_llm_events_audit --limit 150
