# LLM Extraction Testing Framework (Email → Events / Categories)


## 1. Objective

This project designs and implements a **robust, reproducible testing framework** to verify that our event-extraction pipeline—powered by a Large Language Model (LLM)—works reliably on real university mailing-list emails.

The system’s purpose is operational: it **automatically populates a student-facing website** with up-to-date and correctly structured event information (e.g., talks, workshops, deadlines-as-announcements). For students, correctness is critical because the website is used to make time-sensitive decisions (attendance planning, registration, room finding, travel time). Incorrect or missing details (wrong date/time, wrong location, invented speaker, or missing registration link) directly reduce trust and can cause students to miss events or show up at the wrong time/place.

The testing framework evaluates whether the LLM pipeline correctly:

1. **Detects relevance**: determines whether an email contains one or more events that should appear on the website (and correctly identifies non-event emails as such).
2. **Extracts structured information**: converts unstructured email text (and optionally linked URL content) into a consistent event schema (title, date/time, location, URL, organizer, etc.).
3. **Supports auditability**: keeps extraction outputs traceable back to the source email so errors can be debugged and systematically reduced over time. (This “provenance” requirement became a key lesson from the baseline offline benchmark.) 

### Why an explicit testing framework is necessary

LLM-based extraction is powerful but can fail in predictable ways:
- **Hallucinations** (invented details not supported by the email),
- **Format mistakes** (wrong year/day/month, timezone confusion),
- **Omissions** (missing location or registration requirement despite being present),
- **Over-triggering** (extracting “events” from administrative notices).

Because manual inspection of large email corpora does not scale, the framework is designed around:

- A **small, high-quality gold dataset** (manually labeled subset) to provide ground truth.
- **Automated evaluation metrics** to measure performance consistently across runs.
- Optional **LLM-as-a-judge** scoring for cases where strict string matching is insufficient (e.g., paraphrased titles, semantically equivalent locations), while still keeping evaluation outputs structured and auditable.

### Practical constraints reflected in the design

The framework is built to remain usable under two real constraints already observed in the initial offline benchmark:

- **Limited LLM-call budget**: evaluation should minimize repeated calls by producing “frozen” artifacts that can be re-scored locally without re-running extraction.
- **Privacy constraints**: university emails must not be committed publicly; evaluation data containing raw email text remains local and gitignored. 


---

## 2. High-Level Approach

### 2.1 End-to-End Data Flow (Reproducible Pipeline)

This framework follows a **fixed two-layer dataset strategy** designed to balance realism, manual effort, and reproducibility.

- **Layer A (Broad sample)**: we download a moderate number of real emails (**initially 150**) to capture realistic variation (newsletters, single-event announcements, administrative messages).
- **Layer B (Gold set)**: from this pool, we select a smaller, representative subset (**~20 emails**) and manually label it to create a high-quality ground truth for evaluation.

This separation ensures that the evaluation is both realistic (based on real inbox data) and controllable (small enough to label carefully and reuse across experiments).

The pipeline is executed as follows:

1. **Download raw emails (150 emails)**
   - Emails are downloaded automatically from the source mailbox.
   - Each email is stored as a standalone artifact containing raw text and metadata.
   - An index file is generated to enable deterministic filtering, sampling, and reuse.

2. **Pre-filter emails to event candidates**
   - A rule-based pre-filter is applied to the raw email pool to identify emails likely to contain events.
   - This step reduces noise by removing clearly irrelevant emails before manual inspection.
   - The output is a reduced candidate set from which the gold set is selected.

3. **Select the gold set (~20 emails)**
   - From the candidate set, a fixed subset of approximately 25 emails is selected.
   - The selection is deliberately diverse:
     - single-event announcements,
     - multi-event newsletters,
     - borderline or ambiguous cases,
     - non-event emails (negative examples).
   - Once selected, the gold set is frozen and reused unchanged across all experiments.

4. **Define important evaluation categories**
   - A reduced category taxonomy is defined specifically for evaluation.
   - Categories are chosen to reflect meaningful distinctions for students using the website, while remaining stable and easy to label.
   - This taxonomy is independent of any fine-grained production categories.

5. **Manually label the gold set (ground truth creation)**
   - Each gold email is manually annotated with:
     - whether it contains relevant event(s),
     - the extracted structured event fields (title, date, time, location, URL),
     - the assigned evaluation category.
   - This labeled dataset serves as the authoritative reference for evaluation.

6. **Run extraction model(s)**
   - The event-extraction pipeline (LLM-based) is run on the frozen gold set.
   - All model outputs are stored as strict JSON using a fixed schema.
   - Multiple extraction models or configurations may be run on the same gold set for comparison.

7. **Evaluate predictions against gold labels**
   - Predictions are compared against the gold annotations.
   - Deterministic matching is used wherever possible (e.g., dates, URLs).
   - An LLM-as-a-judge is used only when semantic comparison is required (e.g., paraphrased titles or equivalent locations).
   - Detection, extraction, and category-level metrics are computed.

8. **Export evaluation results**
   - Results are exported in two formats:
     - **JSON** for automated analysis, regression testing, and reproducibility.
     - **Excel/CSV** for manual inspection, debugging, and presentation.

---

### 2.2 Download Strategy: Batched and Idempotent by Design

Emails are downloaded **in batches**, and the download process is explicitly designed to be **idempotent**.

This is not an optional design choice—it is required to ensure reproducibility and dataset stability.

**What we do:**
- Emails are downloaded in multiple batches until the target size (150 emails) is reached.
- Each email is written to disk exactly once.
- Re-running the download script does not duplicate or overwrite existing emails.

**Why batching is used:**
- It avoids failures due to rate limits or temporary connection issues.
- It allows the download process to be paused and resumed safely.
- It simplifies debugging by isolating problems to specific batches.

**Why idempotency is enforced:**
- The raw dataset must remain stable across experiments.
- Evaluation results must be attributable to model changes, not data drift.
- Gold set selection depends on a fixed underlying raw pool.

---

### 2.3 Email Storage Format (Fixed Design Choice)

Each downloaded email is stored as **one file per email**, keyed by a stable identifier.

- Primary identifier: `message_id` (if available).
- Fallback identifier: deterministic hash of `(sender, subject, date_received, body_snippet)`.

**Storage layout:**
- `data/raw_emails_150/<email_id>.json`
  - full metadata (sender, subject, date_received, message_id)
  - raw email body text (and optional HTML)
- `data/raw_emails_150/index.json`
  - list of all email IDs with minimal metadata for filtering and sampling

This structure is fixed and intentional.

**Why this design is used:**
- Pre-filtering and gold set selection operate on the index without re-downloading emails.
- Each prediction and evaluation result can be traced back to a specific source email.
- Dataset versions can be compared cleanly across runs.

---

### 2.4 Fixed Parameterization (Initial Setup)

For the first stable evaluation setup, the following parameters are fixed:

- Raw email pool size: **150 emails**
- Gold set size: **~20 emails**

These values are chosen to:
- allow fast iteration during development,
- keep manual labeling effort reasonable,
- provide sufficient diversity to expose common failure modes.

Once the framework is stable, the raw pool can be expanded (e.g., to 200+ emails) and the gold set enlarged without changing the evaluation logic.

## 2.5 Implementation Starts Here: Batched, Idempotent Email Download

Before we finalize categories and gold-labeling, we will first implement the **data acquisition layer** in a way that is:

- **Batched** (so we can stop/resume safely and avoid IMAP instability),
- **Idempotent** (re-running does not duplicate emails),
- **Traceable** (each downloaded email has a stable identifier and metadata),
- **Evaluation-ready** (the storage format supports later filtering, sampling, and gold-set freezing).

This section specifies exactly what we will build next and how it integrates with the existing baseline code.

---

### 2.5.1 Baseline (What We Already Have)

We currently have a working baseline function `download_latest_emails(limit=...)` that:

- connects via IMAP,
- fetches the latest emails,
- extracts plain text (falls back to HTML),
- filters by keywords (Rundmail / WiWiNews),
- optionally fetches URL content and appends it,
- writes per-email `.txt` and a combined `all_emails.txt`.

This is useful for quick manual tests, but it is not ideal for evaluation because:
- files are overwritten / re-created each run,
- emails are not stored with stable IDs,
- combined format is hard to index and filter deterministically,
- batching/resuming is not supported.

Therefore, we implement a new downloader **alongside** the baseline (we do not remove the baseline).

---

### 2.5.2 What We Will Implement Now

We will implement a new script that downloads emails in batches until a target is reached (e.g., 150), and stores them as:

- **one JSON file per email**
- plus a single **index file** describing the dataset

#### Target storage structure (fixed)

- `evaluation/data/raw_emails_105/emails/<email_id>.json`
- `evaluation/data/raw_emails_105/index.json`

Each email JSON contains:
- `email_id` (stable key; message-id preferred),
- `message_id`, `imap_uid`,
- `subject`, `from`, `date`,
- `body_text`,
- optional `url_contents` and `url_content_block` (if we decide to store URL expansions now),
- optional `filter_reason` (why it was included).

This dataset becomes the foundation for:
- candidate pre-filtering,
- gold set selection,
- extraction runs,
- evaluation and auditing.

---

### 2.5.3 Batch Strategy (What We Will Do)

We will download **newest-first**, in repeated batches, until we collect the target number of **kept** emails.

- Default target: **150 kept emails**
- Default batch size: **20 fetched emails per batch**
- We *keep* only emails that pass the filter (Rundmail/WiWiNews), consistent with baseline.
- We skip emails already downloaded (idempotency) using the stable `email_id`.



---

## 3. Category Reduction Rationale

Production systems often use many fine-grained categories. For evaluation, this is counterproductive because:
- Category boundaries become subjective.
- Inter-annotator agreement drops.
- Evaluation metrics become noisy.

Therefore, we define a **small, stable evaluation taxonomy** focused on user intent.

---

## 4. Evaluation Taxonomy (Important Categories)

The reduced category set used **only for evaluation**:

1. Academic Talk / Lecture  
2. Workshop / Training  
3. Conference / Multi-session Program  
4. Career / Recruiting  
5. Social / Networking  
6. Culture / Arts  
7. Sports / Outdoor  
8. Administrative / University Info  
9. Other Event  
10. No Relevant Event  

---



## 6. Gold Set Design

### 6.1 Gold Set Size

- ~25 emails
- Chosen to maximize coverage of failure modes:
  - Single-event emails
  - Multi-event newsletters
  - Ambiguous emails
  - Non-event emails (negative examples)

### 6.2 Gold Annotation Fields

For each email:

- `email_id`
- `subject`
- `sender`
- `date_received`
- `raw_text`
- `contains_event` (boolean)
- `events[]`:
  - `title`
  - `start_date`, `end_date`
  - `start_time`, `end_time`
  - `location`
  - `url`
  - `category_eval`
  - optional `notes`

---

## 7. Two-Step LLM Strategy

### 7.1 Step A: Extraction Model

- Primary LLM (e.g., Gemini).
- Outputs **strict JSON** following a fixed schema.
- Responsible only for extraction, not evaluation.

### 7.2 Step B: Judge Model

- Secondary LLM (e.g., GPT).
- Compares prediction JSON with gold JSON.
- Handles semantic equivalence (titles, locations).
- Outputs structured evaluation decisions only.

### 7.3 Motivation

- Reduces self-evaluation bias.
- Improves handling of paraphrases and ambiguity.
- Allows cross-model robustness testing.

---

## 8. Evaluation Metrics

### 8.1 Email-Level Detection

- Accuracy
- Precision / Recall
- False positives (event detected where none exists)
- False negatives (missed event emails)

### 8.2 Event-Level Extraction

- Event Precision / Recall / F1
- Matching rules:
  - Date overlap + title similarity
  - URL match (if available)
  - Judge LLM for conflicts

### 8.3 Field-Level Accuracy

- Date accuracy
- Time accuracy
- Location accuracy
- URL accuracy

### 8.4 Category Evaluation

- Category accuracy
- Confusion matrix
- Macro-F1 across categories

### 8.5 Robustness

- Run extractor multiple times
- Measure output stability
- Variance of metrics across runs

---

## 9. Implementation Plan

### 9.1 Folder Structure

project/backend/
evaluation/
README.md
configs/
eval_taxonomy.json
model_configs.json
data/
raw_emails_200/
candidates/
gold_25/
predictions/
reports/
scripts/
01_download_emails.py
02_prefilter_emails.py
03_select_gold_set.py
04_run_extraction.py
05_build_gold_template.py
06_run_evaluation.py
07_export_excel.py
lib/
parsing.py
normalization.py
matching.py
metrics.py
judge_client.py


---

## 10. Script Responsibilities

### 10.1 `01_download_emails.py`
- Download ~200 emails.
- Store raw text and metadata.

### 10.2 `02_prefilter_emails.py`
- Rule-based keyword filtering (DE + EN).
- Optional lightweight LLM binary filter.
- Output candidate email list.

### 10.3 `03_select_gold_set.py`
- Stratified selection of ~25 emails:
  - Single-event
  - Multi-event
  - Ambiguous
  - Negative examples

### 10.4 `05_build_gold_template.py`
- Generate annotation template JSON.
- Manually filled once.

### 10.5 `04_run_extraction.py`
- Run extractor model(s).
- Save structured predictions.

### 10.6 `06_run_evaluation.py`
- Normalize fields.
- Match predicted and gold events.
- Compute metrics.
- Call judge model if needed.

### 10.7 `07_export_excel.py`
- Export evaluation summary to Excel / CSV.

---

## 11. Data Formats

### 11.1 Gold JSON Example

```json
{
  "schema_version": "1.0",
  "emails": [
    {
      "email_id": "email_001",
      "contains_event": true,
      "events": [
        {
          "title": "Data Science Workshop",
          "start_date": "2026-01-22",
          "start_time": "18:00",
          "end_date": "2026-01-22",
          "end_time": "20:00",
          "location": "Room 101",
          "url": "https://example.com",
          "category_eval": "Workshop / Training"
        }
      ]
    }
  ]
}
