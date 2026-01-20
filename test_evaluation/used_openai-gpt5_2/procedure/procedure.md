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

- **Hallucinations** (invented details not supported by the email)
- **Format mistakes** (wrong year/day/month, timezone confusion)
- **Omissions** (missing location or registration requirement despite being present)
- **Over-triggering** (extracting “events” from administrative notices)

Because manual inspection of large email corpora does not scale, the framework is designed around:

- A **small, high-quality gold dataset** (manually labeled subset) to provide ground truth.
- **Automated evaluation metrics** to measure performance consistently across runs.
- Optional **LLM-as-a-judge** scoring for cases where strict string matching is insufficient (e.g., paraphrased titles, semantically equivalent locations), while still keeping evaluation outputs structured and auditable.

### Practical constraints reflected in the design

The framework is built to remain usable under two real constraints observed during initial development:

- **Limited LLM-call budget**: evaluation should minimize repeated calls by producing “frozen” artifacts that can be re-scored locally without re-running extraction.
- **Privacy constraints**: university emails must not be committed publicly; evaluation data containing raw email text remains local and gitignored.

---

## 2. High-Level Approach

### 2.1 End-to-End Data Flow (Reproducible Pipeline)

This framework follows a fixed two-layer dataset strategy that balances realism, manual effort, and reproducibility.

- **Layer A (Broad sample dataset)**: we download **150 relevant emails** from the mailbox (filtered to the target mailing formats, e.g., Rundmail/WiWiNews) to capture realistic variation (newsletters, single-event announcements, administrative messages).
- **Layer B (Gold set)**: from this dataset, we select a smaller representative subset (**~20 emails**) and manually label it to create a high-quality ground truth for evaluation.

The pipeline is executed as follows:

1. **Acquire the raw dataset (150 emails)**
   - Emails are downloaded automatically via IMAP.
   - The download is implemented in a batched and idempotent way to ensure that the dataset is stable and reproducible.
   - Emails are stored as standalone artifacts (per-email files) plus a dataset manifest for deterministic filtering, sampling, and repeatable experiments.

2. **Pre-filter to event candidates**
   - A lightweight rule-based filter is applied to identify emails likely containing events.
   - This reduces noise before manual selection of the gold set.
   - The output is a candidate subset used for gold-set sampling.

3. **Select the gold set (~20 emails)**
   - From the candidate subset, ~20 emails are selected to cover:
     - single-event announcements,
     - multi-event newsletters,
     - borderline or ambiguous cases,
     - negative examples (non-event emails).
   - The gold set is frozen so repeated experiments remain comparable.

4. **Define important evaluation categories**
   - A reduced category taxonomy is defined specifically for evaluation.
   - Categories reflect meaningful distinctions for students using the website and are kept stable to reduce subjectivity.

5. **Create ground truth labels**
   - Each gold email is manually annotated with:
     - whether it contains relevant event(s),
     - structured event fields (title, date, time, location, URL),
     - evaluation category.

6. **Run extraction model(s)**
   - The LLM-based extraction pipeline is run on the frozen gold set.
   - Outputs are stored as strict JSON following a fixed schema.

7. **Evaluate predictions against gold**
   - Predictions are compared against gold labels using deterministic matching where possible.
   - An LLM-as-a-judge is used only when semantic comparison is required (e.g., paraphrased titles or equivalent locations).
   - Detection, extraction, and category metrics are computed.

8. **Export evaluation artifacts**
   - Results are exported as:
     - **JSON** (machine-readable; supports regression testing)
     - **Excel/CSV** (human-readable; supports manual review and debugging)

---

### 2.2 Step 1 Completed: Batched, Idempotent Email Download (150 Emails in 5 Batches)

We implemented the dataset acquisition step first to ensure all later evaluation steps operate on a stable and auditable dataset.

**Goal (fixed):**
- Download **150 kept emails** and store them in **5 batches of 30** for manageable review and labeling.

**What “150 kept emails” means:**
- The downloader scans the inbox newest-first and applies the configured filter (e.g., Rundmail/WiWiNews).
- Only emails passing the filter are saved (“kept”).
- If the inbox contains many non-matching emails, the downloader may scan more than 150 messages to collect 150 kept ones.

**Batching design (fixed):**
- `batch_01` … `batch_05`, each containing exactly **30 kept emails**.
- Batches are created as derived outputs to support fast, structured human review.

**Idempotency (required):**
- Re-running the script does not duplicate stored emails.
- Each email is keyed by a stable identifier (prefer `message_id`, otherwise a deterministic fallback hash).
- This guarantees that the dataset remains stable across repeated runs, enabling reproducible experiments.

#### Stored artifacts and why they exist

The downloader produces three storage folders plus a dataset manifest:

1. **Per-email JSON (`emails_json/`) — canonical dataset (most important)**
   - One JSON file per email containing stable identifiers, metadata, and extracted plain-text body.
   - This is the primary input for later filtering, gold-set selection, per-email extraction, and evaluation matching.

2. **Per-email TXT (`emails_txt/`) — human-readable inspection**
   - One text file per email with headers (Subject/From/Date) and body text.
   - This supports fast manual checking and debugging without opening JSON.

3. **Batch TXT (`batches/`) — labeling convenience**
   - One combined text file per batch, each containing 30 emails in a readable concatenated format.
   - These files are designed for “batch-by-batch” review and labeling workflows.

4. **Dataset manifest (`index.json`) — reproducibility + deduplication (most important)**
   - Lists all `email_id`s in the dataset and stores minimal metadata.
   - Stores the batch assignment mapping (`batch_01` → list of email_ids, etc.).
   - Enables idempotent downloads (skip already-downloaded emails) and deterministic sampling for the gold set.


---

## 3. Controlled Event Extraction Using the LLM

After the dataset acquisition step is completed, the next phase focuses on **controlled use of the LLM** to extract events from the downloaded emails while respecting practical constraints such as limited API request budgets and model costs.

Because calling an LLM on the entire dataset at once is neither cost-efficient nor analytically useful at this stage, we deliberately proceed **batch-by-batch**. This allows us to observe extraction behavior, failure modes, and output structure early, before scaling to the full dataset.

### 3.1 Rationale for Batch-wise Extraction

The raw dataset is organized into **5 batches of 30 emails**. These batches serve three purposes:

1. **Cost control**  
   LLM requests are limited and expensive. Processing one batch at a time ensures that we do not exhaust the request budget before understanding model behavior.

2. **Early validation of extraction behavior**  
   By starting with `batch_01`, we can observe:
   - how many events the LLM extracts,
   - whether it over-extracts (hallucinates events),
   - whether it misses obvious events,
   - how it handles newsletters with multiple events.

3. **Iterative refinement**  
   Observations from early batches guide prompt adjustments, schema refinements, and normalization rules before processing later batches.

For these reasons, **`batch_01` is processed first**, followed by subsequent batches only after the extraction behavior is understood and deemed acceptable.

---

### 3.2 Event Extraction Procedure (Per Batch)

For each batch (starting with `batch_01`):

1. **Load the batch text**
   - The combined batch file (e.g., `batch_01.txt`) is used as input.
   - This file contains 30 clearly separated email blocks, preserving source context.

2. **Run the existing extraction pipeline**
   - The batch text is passed to the existing LLM-based event extraction function implemented in `backend/services`.
   - No modification of production extraction logic is performed at this stage.

3. **Collect extracted events**
   - The LLM may extract:
     - zero events,
     - one event,
     - or multiple events per email.
   - This output is not yet judged for correctness; it is treated as a candidate set.

4. **Store extraction results**
   - Results are stored in two parallel formats:
     - **JSON** (machine-readable, used for evaluation and later LLM judging),
     - **Excel/CSV** (human-readable, used for inspection and manual reasoning).

This process is repeated batch-by-batch, allowing controlled expansion of the extracted event pool.

---

### 3.3 Storage of Extracted Information (Evaluation-Critical Fields)

To support both automated evaluation and human inspection, extracted events are stored in two synchronized representations. The storage design is centered around the **fields that are most critical for student-facing correctness** (calendar usability, registration, attendance logistics, and trust).

#### 3.3.1 JSON Output (Authoritative for Evaluation)

A structured JSON file is created per batch, containing only the **events actually extracted** by the LLM. This JSON is the authoritative artifact used for automated checks, metric computation, and later LLM-as-a-judge comparisons.

Each extracted event record must include the following fields because they directly determine whether students can reliably attend or register:

**Core “must-check” fields**
- `Title`
  - Must be recognizable and calendar-suitable.
  - Must not be a full-sentence summary.
  - Must not merge two different events into one title.
- `Start_Date`, `Start_Time` (and `End_Date`, `End_Time` when present)
  - Wrong start date/time is the most damaging error.
  - If unknown or ambiguous → set to `null` (no guessing).
- `Location`
  - Must not hallucinate a physical address for online events.
  - Must follow the **Location TBA rule**: if the email indicates the location will be announced later (e.g., “Ort wird bekanntgegeben”), then location-related fields must consistently be set to “Location TBA”.
- `Registration_Needed`, `Registration_URL`
  - Must satisfy strict consistency constraints:
    - If `Registration_URL` exists → `Registration_Needed` must be `true`.
    - It must never be the case that `Registration_Needed` is `false` while `Registration_URL` is present.
- `Meeting_URL`
  - If a Zoom/Teams/Webex/Meet link exists, it must be placed in `Meeting_URL`.
  - It must not be mixed into `URL` or `Registration_URL`.
- URL separation constraints:
  - `URL` (general event info) must not equal `Registration_URL` or `Meeting_URL`.
  - `Registration_URL` and `Meeting_URL` must not be the same.

**Role disambiguation fields**
- `Speaker` vs `Organizer`
  - Mislabeling speakers is common and reduces credibility on a student-facing website.
  - Signature/contact names must not be incorrectly used as speakers unless explicitly stated.

**Provenance fields (required for traceability and later judging)**
- `source_batch` (e.g., `batch_01`)
- `source_email_id` (stable ID from the raw dataset index)
- Optional: `source_email_position` (which email block within the batch file) to make audits faster.

**Recommended JSON layout**
- One file per batch: `predictions/batch_01.events.json`
- A merged file later: `predictions/all_batches.events.json`

This JSON format is designed so that it can later be:
- compared directly against gold labels,
- evaluated via automated rule checks and metrics,
- passed to an LLM-as-a-judge for semantic comparisons (e.g., title equivalence),
- merged across batches into a single prediction dataset.

---

#### 3.3.2 Excel / CSV Output (Human Inspection)

In parallel, an Excel or CSV file is generated with one row per extracted event. This file supports fast inspection and debugging without reading JSON.

Typical columns include:

- Batch ID
- Email ID
- Event Title
- Start Date
- End Date
- Start Time
- End Time
- Location
- Registration Needed
- URL
- Registration URL
- Meeting URL
- Speaker
- Organizer
- Notes (free-text)

This format allows rapid:
- sanity checks and spot review,
- sorting/filtering by missing fields,
- identification of systematic extraction errors (e.g., time parsing issues or URL misclassification).

---

### 3.4 Filtering to Relevant Event Emails (Reducing Evaluation Load)

To avoid overwhelming later evaluation steps (and the LLM-as-a-judge), we explicitly filter the dataset after extraction.

**Rule (fixed):**
- Only emails that produced at least one extracted event are retained for detailed review and evaluation.

This ensures that:
- non-event emails do not clutter evaluation inputs,
- LLM judging focuses only on meaningful extraction decisions,
- context sent to the judge remains compact and interpretable.

The filtered evaluation set consists of:
- the extracted event JSON (per batch),
- the corresponding source email texts (from the batch `.txt` files),
- and references to original `email_id`s in `index.json`.

---

### 3.5 Multi-Event Emails: What We Check and How We Evaluate

A key difficulty in university mailing lists is that many emails contain **multiple events**, especially newsletters or seminar series announcements. This is a critical evaluation dimension because multi-event failure modes (merging, missing, or duplicating events) directly harm website usefulness.

#### 3.5.1 Expected Multi-Event Behavior

For emails that clearly contain multiple distinct events, the LLM should:
- output **multiple event objects** (not a single merged event),
- keep each event’s `Title`, `Start_Date/Time`, and `Location` specific to that event,
- use the event linking mechanism correctly when applicable:
  - `Event_Type` ∈ {`main_event`, `sub_event`}
  - `Main_Event_Temp_Key` links sub-events to a parent main-event.

#### 3.5.2 Multi-Event Evaluation Checks

We evaluate multi-event handling using three complementary checks:

1. **Event count sanity check (coverage)**
   - For selected multi-event emails in the gold set, we record the expected number of events.
   - We compare expected vs extracted counts to identify under-extraction or over-splitting.

2. **Hierarchy validity checks (automatic constraints)**
   - There must never be a `sub_event` without a corresponding `main_event` that shares the same `Main_Event_Temp_Key`.
   - `Main_Event_Temp_Key` must be non-empty for all events.
   - In a clear series/newsletter, the output should contain at least one `main_event` when sub-events exist.

3. **Merge and duplication checks**
   - Detect whether clearly distinct items were merged into one event (often visible via overly broad titles or mixed date/time fields).
   - Detect duplicates: near-identical events with the same title and date/time repeated.

These checks are intentionally designed to be:
- easy to compute automatically,
- aligned with the schema constraints,
- defensible as “student-impact” validation (multi-event parsing is a known real-world failure mode).

---

### 3.6 Why This Step Is Critical Before Formal Evaluation

This controlled extraction phase serves as a bridge between raw data and formal evaluation:

- It verifies that the extraction pipeline produces usable structured outputs on real emails.
- It surfaces common failure patterns early (hallucinated times, merged events, wrong URL classification).
- It defines the exact subset of emails that will later be evaluated in detail, keeping both human labeling and LLM-judge usage efficient.

Only after this step do we proceed to:
- finalize the evaluation category taxonomy (separately from UI image keys),
- construct gold labels for selected emails,
- and run systematic metric-based evaluation at email-level and event-level.

---



## 4. Controlled Batch-wise Event Extraction (Implementation Status)

After completing dataset acquisition and defining evaluation-critical fields, we implemented a **controlled, batch-wise extraction phase** that applies the existing LLM-based event extractor to the email dataset in a way that is reproducible, auditable, and compatible with strict API limits.

This section documents **what was implemented, how it is executed, and which artifacts are produced**, so the full process remains transparent and easy to reason about.

---

### 4.1 Rationale for Batch-wise Execution

The extraction phase is intentionally executed **one batch at a time** for the following reasons:

- **API rate and daily request limits**: the Gemini model used for extraction has a low requests-per-minute and requests-per-day limit. Running one batch per invocation ensures we stay well within these limits.
- **Early error detection**: processing `batch_01` first allows inspection of extraction behavior (number of events, common errors) before committing further requests.
- **Reproducibility**: each batch execution produces a frozen set of artifacts that can be reviewed later without re-running the LLM.

Each batch contains **30 emails**, and the complete dataset consists of **5 batches (150 emails)**. The same procedure is applied sequentially to `batch_01`, `batch_02`, …, `batch_05`.

---

### 4.2 Execution Mechanism

For each batch, a dedicated runner script is executed from the project root:

```bash
python -m backend.tests.evaluation.run_extract_batch_existing_service --batch batch_01
```
This script:

- Loads the list of email IDs belonging to the specified batch from the dataset index.

- Reconstructs the exact concatenated email format expected by the existing LLM extraction prompt.

- Calls the existing extraction function in backend/services (no modifications to the production prompt or schema).

- Writes all outputs to a new, timestamped result directory.

### 4.3 Output Structure (Per Batch)

For each batch execution, a new folder is created under:

`backend/tests/evaluation/predictions/`

**Example:** `batch_01_20260119_143210/`

This folder contains four files, each serving a distinct purpose.

---

#### 4.3.1 input_sent_to_llm.txt (Audit Artifact)
* **Purpose:** Contains the exact text sent to the LLM for this batch.
* **Content:** Includes all 30 emails in the batch, concatenated using the fixed email block format.
* **Utility:** Preserved for auditability and debugging (e.g., “what did the model actually see?”).
* **Constraint:** This file is not intended for evaluation or sharing; it exists to guarantee reproducibility.

#### 4.3.2 events_full.json (Raw Model Output)
* **Purpose:** Contains the complete JSON output returned by the LLM.
* **Content:** Includes all fields produced by the extraction schema.
* **Utility:** Serves as a debugging and fallback artifact in case additional fields are needed later.
* **Constraint:** This file represents the model’s output before any evaluation-focused filtering.

### 4.3.3 events_filtered.json (Evaluation-Focused Output)
* **Purpose:** Contains a reduced representation of each extracted event.
* **Content:** Includes only the fields identified as critical for student-facing correctness, such as:
    * `title`
    * `start/end date and time`
    * `location`
    * `registration requirements and URLs`
    * `meeting links`
    * `speaker/organizer`
    * `multi-event structure fields` (Event_Type, Main_Event_Temp_Key)
* **Utility:** This JSON file is the primary artifact used in later evaluation steps and for external review.

### 4.3.4 events_filtered.xlsx (Human Inspection)
* **Purpose:** Spreadsheet version of `events_filtered.json`.
* **Content:** One row per extracted event.
* **Utility:** Enables manual sorting, filtering, and quick inspection.
* **Constraint:** This file is intended for human analysis only and is not required for automated evaluation.

---


## 5. Gold-Set Construction and Packaging (25 Emails)

After running LLM extraction batch-by-batch, the dataset contains a large number of extracted events (often 10–15 events per batch, which would lead to 50–75+ events overall). Manually evaluating the full set is not feasible, and sending all emails and all extracted events to an external judge model would be inefficient and exceed practical context and privacy limits.

Therefore, we construct a **small, representative gold set** of emails for detailed evaluation.

### 5.1 Objective

The gold set is designed to:
- keep evaluation manageable (**~25 emails**),
- cover the most important student-impact failure modes (wrong dates/times, wrong locations, missing registration links, incorrect online meeting links),
- explicitly include difficult cases such as **multi-event newsletters** and **event series** where hierarchy handling matters.

### 5.2 Stratified Sampling Strategy (5 Emails per Batch)

Instead of purely random sampling, we use a **stratified selection** that guarantees coverage of high-risk cases.

For each batch (`batch_01` … `batch_05`) we select 5 emails:

1. **Multi-event / newsletter case**
   - An email where the extractor produced multiple events (e.g., ≥3) and/or where sub-events appear.
2. **Registration-heavy case**
   - An email where registration is required or a registration link is present.
3. **Online/hybrid case**
   - An email containing a meeting link (Zoom/Teams/Webex/Meet).
4. **Location-risk case**
   - An email with “Location TBA” behavior or unclear location signals.
5. **Borderline / negative case**
   - An email with event-like cues (date/time/location keywords) but no extracted events, or an extracted event with missing critical time/date fields.

This produces a final evaluation set of **25 emails** (5 batches × 5 emails).

### 5.3 Handling Multi-Event Emails in the Gold Set

Multi-event emails are explicitly included because they are a known failure mode:
- Extractors may merge distinct events into one output,
- miss sub-events entirely,
- or produce incorrect main/sub-event linking.

Including at least one multi-event email per batch ensures that:
- multi-event splitting is tested systematically,
- the main/sub-event structure fields (`Event_Type`, `Main_Event_Temp_Key`) can be evaluated.

### 5.4 Packaging for Efficient Evaluation (Minimal Artifacts)

To keep evaluation inputs compact, we do not export full batch files. Instead, we produce a “packaged” dataset containing only:

- the selected email texts (one file per selected email), and
- the corresponding extracted event predictions (JSON).

This enables later evaluation and LLM-as-a-judge comparisons without sharing the full email corpus.

### 5.5 Output Artifacts

The selection step produces:

- `backend/tests/evaluation/gold_selection/selection_25.json`
  - manifest of selected emails and selection reasons per batch
- `backend/tests/evaluation/gold_selection/selection_report.xlsx`
  - human-readable overview of the selection coverage and flags
- `backend/tests/evaluation/gold_selection/pack_for_chatgpt/`
  - `email_001.txt`, ..., `email_025.txt` (selected email texts)
  - `email_001_pred.json`, ..., `email_025_pred.json` (predicted extracted events)

These artifacts become the fixed input for the final evaluation and judging steps.




---

## 6. Manual Judging on the Gold Set (25 Emails)

After the gold set was constructed and packaged, we executed the final evaluation step using a **manual LLM-judge workflow**. This was chosen deliberately because it provides the strongest combination of:

- **interpretability** (each decision can be explained and audited),
- **low cost** (no additional API infrastructure required),
- **reproducibility** (the exact judged inputs are frozen in files),
- **privacy control** (evaluation is performed locally on a small subset).

This step verifies whether the extracted event information is correct in the context of what students actually need.

---

### 6.1 Evaluation Method (Binary, Field-Level)

For each selected email in `pack_for_chatgpt/`, we evaluated the LLM predictions using a strict **binary scoring scheme**.

Each predicted event is checked against the source email for the following student-critical fields:

- **Title**
- **Start_Date / Start_Time** (and End_* where applicable)
- **Location** (including “Location TBA” handling)
- **Registration_Needed + Registration_URL consistency**
- **Meeting_URL placement** (Zoom/Teams/Webex/Meet)
- **URL separation** (`URL` vs `Registration_URL` vs `Meeting_URL`)
- **Speaker vs Organizer** correctness
- **Multi-event correctness** (no merging; correct main/sub linking via `Main_Event_Temp_Key`)

Each field is scored:

- **Correct (1)**  
- **Incorrect (0)**

Special rule (conservative, anti-hallucination):
- If the email does not specify a value and the prediction uses `null`, this counts as **Correct** (“null rather than guessing”).

This provides a transparent correctness definition that is easy to defend academically.

---

### 6.2 Execution Workflow (Using the Packaged Inputs)

The evaluation was performed batch-wise using the fixed gold pack:

- Email source text: `email_###.txt`
- Predicted extracted events: `email_###_pred.json`

For each of the 25 selected emails:
1. The email text and its predicted events were provided to the judge prompt.
2. Each extracted event was scored on the 8 student-critical dimensions.
3. A short justification was recorded for any incorrect field (kept brief for privacy and GitHub suitability).
4. Scores were aggregated at:
   - event level,
   - email level,
   - and batch level.

This structure produces evaluations that can later be recomputed or re-audited without re-running extraction.

---

### 6.3 Summary of Findings (Reduced, Report-Ready)

The results show a **high overall success rate** on the most important operational cases:

- **Single, well-specified event emails** were typically extracted correctly end-to-end.
- **Registration handling** was consistently strong:
  - links and “registration required” logic were usually aligned.
- **Online/hybrid detection** was robust:
  - meeting links were generally assigned correctly to `Meeting_URL`.

Most observed errors were concentrated in a smaller subset of structurally complex emails, mainly involving:

1. **Multi-event modeling (series / overview emails)**
   - The extractor sometimes created an overarching “main event” spanning multiple separate sessions, rather than representing sessions separately.

2. **Over-specific location enrichment**
   - The extractor occasionally added city/country or address details inferred from contact blocks rather than the explicit event location line.

3. **Ambiguous or low-quality email structure**
   - Recruitment-style or overview-style emails frequently mix:
     - deadlines,
     - program periods,
     - optional info sessions,
     - and multiple links.
   - In these cases, “what counts as the event” is inherently ambiguous even for humans.

A key conclusion for the report is that **many low-score cases are driven by email structure and ambiguity**, not by random model failure. The observed error patterns are consistent and addressable via targeted prompt refinements.

---

### 6.4 Why This Outcome Is Considered a Success

This evaluation phase achieved its main objectives:

- It demonstrated that the pipeline works reliably on the dominant student-relevant email class (clean single-event announcements).
- It exposed a small number of systematic and explainable failure modes (multi-event representation and location over-specification).
- It validated the usefulness of the testing framework itself: the workflow produced actionable insights without requiring large-scale manual inspection.

---
