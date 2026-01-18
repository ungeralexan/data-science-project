# LLM Extraction Quality Evaluation (Offline Benchmark)

This document explains **what was done**, **why it was done**, **what problems occurred**, and **how to reproduce the evaluation locally**.

The goal is to make the LLM extraction pipeline **testable, auditable, and reproducible** under two practical constraints:

1. **Limited LLM-call budget** (Gemini API requests were constrained during evaluation).
2. **Privacy** (university mailing-list emails must not be pushed to a public GitHub repository).

All evaluation tooling was implemented under `project/backend/tests/` and was designed **not to modify production code** in `project/backend/services/` and **not to write to the database**.

---

## 1. Purpose of this evaluation

The project extracts structured university events from unstructured mailing-list emails using an LLM (Gemini). Because LLMs can produce:

- **Incorrect fields** (hallucinations, wrong date/time/location, wrong speaker),
- **Incomplete records** (missing information that is present in the email),

we ran an **offline benchmark** to:

- quantify **schema coverage / completeness**,
- enable later **correctness auditing**,
- identify systematic weaknesses for **prompt/model improvements**.

---

## 2. Constraints and design choices

### 2.1 Limited LLM requests
We had a limited number of Gemini API calls available for testing. Therefore, the evaluation was designed to:

- minimize repeated LLM calls,
- create **frozen artifacts** that can be re-evaluated locally without re-calling the LLM.

### 2.2 Privacy and open GitHub repository
University emails cannot be published. Therefore:

- all evaluation outputs containing raw email text are written into a local folder that is **gitignored**,
- only scripts and aggregated evaluation results are committed to GitHub.

### 2.3 No changes to production pipeline
We intentionally did **not** modify production services (`services/`) or any DB pipeline logic.
All evaluation work is done in test scripts under `project/backend/tests/`.

---

## 3. What “quality” means in this benchmark

We consider two quality dimensions:

### 3.1 Completeness (schema coverage)
If an event detail exists in the email (or in URL content fetched from that email), it should be present in the extracted event object.

Examples of completeness errors:
- date missing although explicitly stated,
- location missing though listed,
- registration requirement missing though clearly required.

### 3.2 Correctness (evidence support)
Each extracted field should be **supported by the source email** (or attached URL content).

Examples of correctness errors:
- wrong date/time (format confusion, wrong year),
- wrong location (taken from unrelated text),
- invented speaker/organizer.

**Important:** correctness cannot be fully measured unless each extracted event can be mapped back to its source email (provenance).

---

## 4. Baseline pipeline used in the evaluation (production services)

### 4.1 `services/email_downloader.py`
**Purpose:** Downloads the latest emails via IMAP, extracts text, optionally fetches URL content from links, and builds a combined text file for the LLM.

**Output produced:**
- `EMAIL_TEMP_DIR/all_emails.txt`

**Why this matters:**  
This file represents the **exact raw input** that the extraction LLM sees (email body + URL content blocks).

---

### 4.2 `services/event_recognizer.py`
**Purpose:** Calls Gemini via API and extracts structured event objects from the concatenated email text using a strict JSON schema.

**Why this matters:**  
This is the **system under test**; its output is what would ultimately populate the database and be shown in the frontend.

---

## 5. Baseline evaluation scripts (used successfully)

These scripts were used to generate a reproducible evaluation dataset and compute first quantitative KPIs.

### 5.1 `tests/export_llm_events.py` (local export runner)
**Purpose:** Run one extraction batch end-to-end *without writing to DB*, then store private artifacts locally for analysis.

**What it does:**
1. Calls `download_latest_emails(limit=...)`  
2. Loads `EMAIL_TEMP_DIR/all_emails.txt`  
3. Saves the raw input into `local_eval/` (private)  
4. Calls `extract_event_info_with_llm(all_emails)`  
5. Saves extracted events as JSON (and optional Excel)

**How to run (recommended, robust):**
```bash
cd project/backend
python3 tests/export_llm_events.py --limit 200 --no-excel
```


## Why `python3 tests/...` was used instead of `python -m tests...`

A module-resolution issue occurred on the local machine:

- `ModuleNotFoundError: No module named 'tests'`

Running scripts by file path (`python3 tests/...`) avoids Python package import issues and is reliable across environments.

---

## Artifacts produced by the baseline export (private, gitignored)

- `project/backend/local_eval/all_emails_<timestamp>.txt`
- `project/backend/local_eval/llm_events_<timestamp>.json`
- optional: `project/backend/local_eval/llm_events_<timestamp>.xlsx`

**Outcome:**  
This created a **frozen extraction run** that can be evaluated repeatedly without re-downloading emails or re-calling Gemini.

---

## `tests/summarize_llm_events.py` (KPI summary, no new LLM calls)

**Purpose:** Compute quantitative schema coverage KPIs from the extracted events JSON.

**How to run:**
```bash
cd project/backend
python3 tests/summarize_llm_events.py --json local_eval/llm_events_<timestamp>.json
```

## Outputs produced (baseline KPI evaluation)

**All files below are private and gitignored.**

- `local_eval/reports/missingness_<timestamp>.csv`  
- `local_eval/reports/stats_<timestamp>.json`

*Why this was useful:**  
These files provided **quantitative KPIs immediately** (field missing rates, distributions, basic statistics) **without spending money on a judge model** or running additional LLM calls.

---


## Main weakness discovered in the baseline setup

With a single concatenated extraction run, it is difficult to trace:

> Which extracted event came from which specific email, and what text evidence supports each field.

This makes it hard to evaluate:
- correctness vs email,
- hallucinations,
- completeness relative to the email content.

Therefore, we explored an **auditability extension**.

---

## Auditability extension (experimental scripts)

To support deterministic provenance, two additional scripts were created.  
They attempt to make each event **self-documenting** by adding:

- **`Source_Email_Index`**: which email block produced the event  
- **`Evidence`**: a short quote/snippet supporting the extraction

They also include a **deterministic heuristic prefilter** to reduce obvious non-event emails **without using an LLM**.

---

## `tests/export_llm_events_audit.py`

**Purpose:** Perform a single extraction run that is auditable.

### Key features
- Splits the concatenated email file into explicit email blocks (regex-based).
- Applies a heuristic prefilter to keep only “likely event” emails (no extra LLM calls).
- Runs **one** LLM extraction call on the filtered set.
- Forces additional audit fields:
  - `Source_Email_Index`
  - `Evidence`

### Outputs produced
- `tests/local_eval/all_emails_raw_<timestamp>.txt`  
  Full concatenated email set.
- `tests/local_eval/all_emails_filtered_<timestamp>.txt`  
  Prefiltered subset used for the single LLM call.
- `tests/local_eval/email_index_<timestamp>.json`  
  Subject/from mapping for filtered emails.
- `tests/local_eval/llm_events_<timestamp>.json`  
  Extracted events including `Source_Email_Index` + `Evidence`.
- optional: `tests/local_eval/llm_events_<timestamp>.xlsx`  
  Two sheets: `Events` + `EmailsUsed`.


  ### Reproducible command
```bash
cd project/backend
python -m tests.export_llm_events_audit --limit 150
```


## Problems encountered with the heuristic prefilter (important)

The heuristic prefilter can reduce token load but may reduce recall:

- **False negatives:** real events without explicit cue words  
  (e.g., details only expressed in prose or only present in URL content)
- **False positives:** non-event announcements containing dates/times  
  (e.g., deadlines, surveys, administrative notices)
- **Format and language variation:** university emails vary strongly in structure, phrasing, and language (German/English/mixed)

Because losing recall biases the evaluation dataset, this approach is marked as **experimental** and requires calibration and validation before being used as a default evaluation pipeline.

---

## `tests/build_matched_eval_pack.py`

### Purpose
Build a minimal evaluation “review pack” after extraction (**no new LLM calls**).

### Why it exists
Even with auditable events, reviewers should not scan 200 emails.  
This script extracts **only the emails referenced by extracted events**, enabling efficient and deterministic review.

---

### Inputs
- `llm_events_<timestamp>.json`
- `all_emails_raw_<timestamp>.txt` (preferred)  
  or `all_emails_filtered_<timestamp>.txt`

---

### Outputs
- `<prefix>_matched_emails.txt`  
  Only email blocks referenced by events (based on `Source_Email_Index`).
- `<prefix>_matched_emails_index.json`  
  Subject/from lookup for matched emails.
- `<prefix>_matched_eval.xlsx` (two sheets):
  - **Events** (events + evidence)
  - **MatchedEmails** (only relevant emails, previewed)
- `<prefix>_report.json`  
  Summary counts and a check whether any referenced indices were missing.

---

### Reproducible command
```bash
cd project/backend
python -m tests.build_matched_eval_pack \
  --events-json tests/local_eval/llm_events_YYYYMMDD_HHMMSS.json \
  --emails-txt  tests/local_eval/all_emails_raw_YYYYMMDD_HHMMSS.txt \
  --out-prefix  matched_YYYYMMDD_HHMMSS
```


