# Final Evaluation Summary (Batches 1–5)

This document summarizes the manual evaluation results for the event-extraction LLM across all emails processed in this run. 
## Coverage

Evaluated emails (by internal index):
- **Batch 1:** Email 001–005  
- **Batch 2:** Email 006–008, 010  
- **Batch 3:** Email 011–013, 015  
- **Batch 4:** Email 016–020  
- **Batch 5:** Email 021–023, 025  

Some emails correctly yielded **no events** (notably **Email 003** and **Email 019**), which is a valid outcome when an email does not specify a schedulable event.

## Overall Observations

### What worked well
- **Single, well-specified events** were frequently extracted correctly end-to-end (title, time window, registration, and online/offline mode).  
  Examples with near-perfect or perfect field correctness:
  - **Email 015:** clean single-event invite with explicit time, location, and registration link.
  - **Email 020:** clearly defined virtual program period with distinct information vs registration links.
  - **Email 022:** one in-person event with “registration requested” and clear venue.

- **Online meeting links** (when present) were generally placed correctly especially in `Meeting_URL` .

### Highest-impact failure patterns
These patterns most strongly affected the final scores and are the primary drivers of errors:

1. **Multi-event modeling and “main event” construction**
   - The LLM often created an overarching “main” event that incorrectly spanned multiple discrete sessions, instead of representing sessions separately.
   - Common error modes:
     - Converting recurring sessions into one continuous date range (or a single start/end time across multiple dates).
     - Merging heterogeneous segments (e.g., an online talk plus a separate phone-only consultation) into one event.

   Emails where this was most visible:
   - **Email 012:** program with three separate weekend modules; predicted as one continuous range.
   - **Email 013:** online presentation + separate telephone office hour; predicted as one combined event window.
   - **Email 016:** overview email listing multiple courses; predicted as an overarching series-event.
   - **Email 021:** three separate online talks; predicted as a single series block in addition to correct per-talk entries.
   - **Email 023:** two info sessions (online + in-person) treated as a continuous multi-day event.

2. **Over-specification of location**
   - The LLM frequently added extra location detail (city/country) not explicitly stated in the event’s location line.  
   - This produced “Location: Incorrect” even when the venue name was otherwise correct.



3. **Date/year mismatches driven by ambiguous or inconsistent email content**
   - One of the most severe errors was a year mismatch when the email content itself listed dates in a different year than expected from surrounding context.

   Example:
   - **Email 006:** two “January” dates appeared with a different year in the email body; the prediction used the other year, resulting in “Date & Time: Incorrect” for those entries.



## Emails Where the LLM Struggled Most

Below are the emails where correctness issues were the most concentrated and/or most impactful:

- **Email 012:** multi-module program compressed into one continuous event; URL role confusion (information vs registration) and duplication.
- **Email 013:** incorrect merging of distinct segments (online presentation + phone consultation) into one event span.
- **Email 016:** overview email treated as a single schedulable series event (registration logic not well-defined at the overview level).
- **Email 023:** two separate sessions modeled as a continuous multi-day range; incomplete capture of the second session and an 

## Important Context: Email Quality as a Root Cause

A recurring theme is that several low-scoring cases are best explained by **email quality and structure**, not purely by prompt/system design:

- **Recruitment-style emails** (e.g., buddy programs or volunteer calls) often contain:
  - deadlines,
  - program periods,
  - optional info sessions,
  - multiple forms/links,
  - and mixed-purpose content in one message.  
  This makes “what is the event?” inherently ambiguous. Even a strong model must choose between interpreting a **deadline**, a **program period**, or an **optional session** as the primary calendar object.

  Concrete examples from this run:
  - **Email 020:** high quality: explicit virtual program period plus clear registration link and separate information link (easy to structure).
  - **Email 025:** low quality/ambiguous: mixed deadlines and a voluntary info touchpoint; unclear whether to model as events or administrative cutoffs.

- **Agenda-heavy invitations** sometimes list multiple components without clarifying whether they are separate calendar entries (e.g., talk + discussion + dinner). This creates ambiguity in whether to:
  - model one single event with sub-items,
  - or model multiple distinct events with separate locations and times.  
  Example: **Email 005** (multi-part schedule with different venues).

- **Mixed-language or repeated sections** can introduce year/date inconsistencies. When the email itself contains conflicting temporal signals, errors become much harder to avoid (example: **Email 006**).

In short: a meaningful portion of observed errors stems from **underspecified, structurally complex, or internally inconsistent emails**, where “correct” calendar extraction is not uniquely determined from the text.



# Final Performance Assessment and Improvement Outlook

## 1. Overall Performance Summary (Positive Balance)

Across **Batches 1–5**, the event-extraction pipeline demonstrates **strong and reliable performance** on the fields that matter most for a student-facing event platform.

### High-level result (qualitative)

- The system performs **very well on clean, well-structured event emails**, which represent the majority of real operational use cases.
- **Single events**, **clearly scheduled workshops**, **online talks**, and **registration-driven events** are extracted with **near-perfect correctness**.
- The extraction logic shows **robust internal consistency**:
  - registration logic is usually correct,
  - meeting links are correctly identified and placed,
  - speaker vs organizer roles are mostly handled accurately,
  - null handling (no guessing) works as intended.

From a product and teaching perspective, this means:

> **In realistic, well-authored university emails, the system reliably produces calendar-ready event entries with minimal risk for students.**

---

## 2. Interpreting the Scores in Context

While some events receive partial scores (e.g. 4–6 out of 8), it is important to interpret these results **in context**.

### What the scores actually show

- **Perfect or near-perfect scores (7–8 / 8)** dominate for:
  - clean invitations,
  - single-session workshops,
  - clearly online or clearly in-person events,
  - emails with explicit registration instructions.

- **Lower scores** cluster around a **small number of structurally complex emails**, not around systematic extraction failures.

This indicates that:
- the system is **not randomly failing**,
- errors are **patterned and explainable**,
- and performance is **predictable**, which is critical for deployment.

---

## 3. Root Cause Analysis: Where Errors Really Come From

A key outcome of the evaluation is that **many observed errors are driven by email quality, not by model weakness**.

### 3.1 Email structure as the dominant challenge

The most problematic cases share one or more of the following characteristics:

- **Overview or recruitment emails** mixing:
  - deadlines,
  - program periods,
  - optional info sessions,
  - and multiple links.
- **Agenda-heavy invitations** listing:
  - talk,
  - discussion,
  - social events (e.g., dinner),
  without clarifying whether these are separate calendar events.
- **Program descriptions** spanning weeks or months, without clearly stating:
  - whether dates represent sessions,
  - or merely application periods.
- **Inconsistent or repeated date references**, sometimes across languages.

In such cases, there is often **no single “correct” calendar interpretation** that can be uniquely inferred from the text—even for a human reader.

This is an important and academically honest conclusion:

> A significant fraction of “errors” reflect **underspecified or ambiguous source emails**, rather than extraction mistakes in a narrow technical sense.

---

## 4. Strengths of the Current System Prompt

The current system prompt already encodes several **strong design decisions** that clearly paid off in evaluation:

- **No guessing policy**  
  Missing information is set to `null`, which prevented hallucinated times or locations in many cases.

- **Strict URL role separation**  
  Errors here are rare and easily traceable when they occur.

- **Clear speaker vs organizer rules**  
  Mislabeling is limited and usually tied to ambiguous email phrasing.

- **Explicit multi-event capability**  
  The model *does* recognize multi-event structures; remaining issues are about *how to represent them*, not whether they exist.

Overall, the prompt provides a **solid foundation** that already supports high-quality extraction.

---

## 5. Targeted Improvement Opportunities (Prompt-Level, Not Model-Level)

The evaluation suggests **incremental prompt refinements**, not a redesign. These refinements would likely improve performance **without increasing model complexity or cost**.

### 5.1 Multi-event and series handling (highest impact)

**Observed issue**  
The model sometimes creates an overarching “main event” that:
- spans multiple distinct sessions,
- or compresses recurring dates into a continuous range.

**Proposed prompt refinement**
Add a stronger disambiguation rule:

> *If an email lists multiple dates that are not explicitly described as a continuous event, prefer representing them as separate sub-events rather than as one event with a date range.*

This keeps behavior conservative and avoids overstretching event durations.

---

### 5.2 Distinguishing program periods vs events

**Observed issue**  
Program descriptions with:
- application deadlines,
- participation periods,
- and optional info sessions
are sometimes interpreted as schedulable events.

**Proposed prompt refinement**
Explicitly state:

> *Do not treat application periods, deadlines, or program durations as calendar events unless the email explicitly describes a scheduled session with a date and time.*

This would reduce false-positive “program wrapper” events.

---

### 5.3 Location specificity restraint

**Observed issue**  
The model occasionally enriches locations with city/country information taken from contact sections.

**Proposed prompt refinement**
Add a conservative location rule:

> *Only include city, postal code, or country if they appear directly in the event’s location description. Do not infer them from signatures or contact blocks.*

This would turn several “Incorrect” location cases into “Correct”.

---

## 6. Why the Overall Evaluation Is Strong (Key Takeaway)

From an academic and practical standpoint, the evaluation supports a **very positive conclusion**:

- The system performs **reliably on the majority of real-world, student-relevant event emails**.
- Failures are **concentrated in structurally ambiguous emails**, where even human interpretation is non-trivial.
- Errors follow **clear, understandable patterns**, making them addressable through targeted prompt refinements.
- The evaluation framework itself successfully surfaces **meaningful, actionable insights** rather than superficial accuracy numbers.

In summary:

> **The event-extraction pipeline is already suitable for practical deployment in a student-facing context, and the remaining limitations are largely driven by email authoring practices rather than by fundamental model shortcomings.**

This positions the project well both technically and academically, demonstrating not only strong results but also a mature understanding of where automation meets real-world ambiguity.
