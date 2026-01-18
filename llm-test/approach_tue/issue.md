# LLM Extraction Testing Framework (Email → Events / Categories)

## 1. Objective

The goal of this project is to design and implement a **robust testing framework** to evaluate whether a Large Language Model (LLM) correctly:

1. Detects whether an email contains relevant events.
2. Extracts structured event information accurately.
3. Assigns the **most important categories** correctly (not overly granular ones).
4. Produces stable and reproducible results across runs and models.

Because manual inspection of large email corpora does not scale, the framework relies on:
- A **small, high-quality gold dataset**.
- Automated evaluation metrics.
- Optional **LLM-as-a-judge** evaluation to handle semantic ambiguity.

---

## 2. High-Level Approach

### 2.1 End-to-End Data Flow

1. Download ~200 raw emails.
2. Pre-filter emails likely to contain events.
3. Select ~25 representative emails as a **gold set**.
4. Define a reduced taxonomy of **important evaluation categories**.
5. Manually label the gold set (ground truth).
6. Run one or more extraction LLMs on the gold set.
7. Evaluate predictions against gold labels.
8. Export results as:
   - JSON (machine-readable)
   - Excel/CSV (human-readable)

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

## 5. Mapping Production Categories to Evaluation Categories

Fine-grained production categories are mapped into the evaluation taxonomy.

Example mappings:
- `lecture`, `seminar`, `ai`, `machine_learning` → Academic Talk / Lecture  
- `careerfair`, `company_talk` → Career / Recruiting  
- `meetup`, `party`, `networking` → Social / Networking  

This preserves production detail while ensuring stable evaluation.

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
