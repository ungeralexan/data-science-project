# LLM Extraction Error Patterns (200-email manual review) + Improvemnet systemprompt

This document summarizes recurring failure patterns observed during a manual review of ~200 university emails and 20 extracted events, and provides actionable recommendations—especially for improving the **system prompt** used for event extraction.

---

## Scope

- **Input:** University mailing list emails (German/English mixed; heterogeneous formats)
- **Output schema (fields):**
  - Title, Description, Start_Date, End_Date, Start_Time, End_Time
  - Location, Organizer, Speaker, Registration_Needed, URL
- **Evaluation approach:** Manual ground-truth reading + LLM extraction + second LLM judging field correctness / support

---

## Summary: What works reliably

The LLM performs strongly when fields are **explicitly stated** and unambiguous in the email text:

- **Title** (subject/body match)
- **Start_Date / End_Date** when the year is explicitly stated and only one plausible date exists
- **Start_Time / End_Time** when written as explicit clock times (e.g., `16:15–17:45`, `6:30 PM`)
- **Location** when a concrete place is given (building/room/address or explicit online venue)
- **Organizer** when derivable from sender/signature or “hosted by” phrasing
- **URL** when a visible clickable link exists in the email
- **Registration_Needed** when “Anmeldung erforderlich / nicht erforderlich” is explicitly stated

---

## Failure patterns (structured)

### Pattern P1 — Conflicting or multi-source dates (email vs. prose vs. link)
**Symptom**
- `Start_Date` / `End_Date` becomes unsupported or wrong when multiple dates appear (announcement date, deadline, series dates, link dates).

**Trigger cues**
- Multiple date formats in one mail (`04.12.2025` + `Nov 4th, 2025`)
- URLs containing dates (e.g., blog permalinks)
- Linked pages referencing a different date than the email snippet

**Impact**
- High: wrong calendar entries or forced “unsupported”

**Handlungsempfehlung (system prompt)**
- Instruct a deterministic **date selection rule**:
  - Prefer dates closest to event keywords: `am`, `on`, `statt`, `Uhr`, `von-bis`, `Ort`, `Treffpunkt`
  - Treat dates in URLs as **low-confidence** unless explicitly labeled “Event date”
  - If two plausible event dates remain → output `Start_Date: null` and add a short note to `Description`

---

### Pattern P2 — Missing year in date (“04. Dezember”)
**Symptom**
- `Start_Date` / `End_Date` unsupported due to absent year.

**Trigger cues**
- “Datum: 04. Dezember” without a year
- Email context suggests semester timing, but year not explicit

**Impact**
- Medium to high: event disappears from feed / cannot be scheduled

**Handlungsempfehlung (system prompt)**
- Add explicit rule:
  - **Never guess the year** unless the email itself contains an unambiguous year.
  - If year missing → set date to `null` and append: “Year not specified in email.”
- Optional (pipeline-level, outside prompt): infer year from email timestamp or semester bounds.

---

### Pattern P3 — Academic time notation (c.t., s.t., partial times)
**Symptom**
- `Start_Time` becomes unsupported when only `17 c.t.` or “ab 18 c.t.” is provided.
- Partial times like “von 10” reduce confidence.

**Trigger cues**
- `c.t.` / `s.t.`
- “ab 18 c.t.”, “17 c.t.”, “von 10”

**Impact**
- Medium: lowers time recall, harms calendar export

**Handlungsempfehlung (system prompt)**
- Introduce an explicit policy for academic time:
  - If `c.t.` is present and no minutes given:
    - Extract as `Start_Time_Raw: "17 c.t."` (if you support raw fields), and set `Start_Time: null`
  - If you do **not** support raw fields:
    - Set `Start_Time: null` and add to `Description`: “Time given as 17 c.t. (academic quarter).”
- Optional (post-processing rule, recommended): map `17 c.t.` → `17:15` and `17 s.t.` → `17:00` deterministically.

---

### Pattern P4 — No explicit end time (common in promos)
**Symptom**
- `End_Time` unsupported in many events (only start time given).

**Trigger cues**
- “Beginn 18 Uhr”, “starting at 6 p.m.” without an end time
- Informal invitations

**Impact**
- Low to medium: calendar blocks are incomplete

**Handlungsempfehlung (system prompt)**
- Enforce strict rule:
  - **Do not invent an end time.**
  - Output `End_Time: null` unless explicitly stated.
- Optional (product decision): default duration by category (talk=90min) **outside** the extraction model.

---

### Pattern P5 — Location “will be announced” mistakenly treated as a location
**Symptom**
- Location extracted as incorrect when the email says it will be announced after registration.

**Trigger cues**
- “Location: will be announced…”
- “Ort wird nach Anmeldung bekanntgegeben”

**Impact**
- Medium: misleading location in UI

**Handlungsempfehlung (system prompt)**
- Add a negative constraint:
  - If location contains phrases like:
    - “will be announced”, “to be announced”, “upon registration”, “wird bekanntgegeben”
  - Then set `Location: null` and add a short note to `Description`.

---

### Pattern P6 — Speaker vs. organizer vs. contact confusion
**Symptom**
- `Speaker` often unsupported or misassigned when names appear in signatures or as contacts.
- Some names are “conceived by” or “organized by” rather than speaking.

**Trigger cues**
- Signature blocks with names
- “Kontakt: …”
- “Konzeption: …”
- “powered by / supported by”

**Impact**
- Medium: speaker info missing or wrong

**Handlungsempfehlung (system prompt)**
- Provide strict role definitions and extraction triggers:
  - **Speaker** only if language indicates speaking/presenting:
    - “Vortrag von”, “speaker”, “talk by”, “mit dabei”, “keynote”, “lecture”
  - **Organizer** if host/sender/department/team is responsible:
    - “organisiert von”, “hosted by”, sender org, signature unit
  - **Contact** (if supported) for signature person; otherwise keep in `Description`
- If uncertain: set `Speaker: null`.

---

### Pattern P7 — Registration requirement not explicit
**Symptom**
- `Registration_Needed` unsupported when registration is implied but not stated.

**Trigger cues**
- “more info” links without explicit “register”
- voting instructions or account setup that is not registration

**Impact**
- Medium: UX confusion (users miss registration deadlines)

**Handlungsempfehlung (system prompt)**
- Restrict boolean extraction:
  - `Registration_Needed = true` only if explicit action is required:
    - “Anmeldung erforderlich”, “please register”, “send an email to register”, “Anmeldung bis…”
  - `Registration_Needed = false` only if explicitly stated:
    - “keine Anmeldung nötig”, “no registration required”
  - Otherwise: `Registration_Needed: null` (or “unsupported” depending on schema)

---

### Pattern P8 — URL referenced but not present in visible excerpt
**Symptom**
- `URL` unsupported because email references “link below” but the excerpt contains no URL.

**Trigger cues**
- “Link s. u.”, “weitere Infos unten”, “see link below”

**Impact**
- Low (correct behavior), but reduces completeness

**Handlungsempfehlung (system prompt)**
- Add explicit instruction:
  - Only extract URLs that are **explicitly present** in the provided text.
  - If referenced but missing, set `URL: null` and optionally add: “Email references a link not included in text.”

---

## System Prompt Improvements (copy-paste ready)

### A) Add hard constraints (anti-hallucination)
- Do **not** invent:
  - missing year
  - end times
  - locations
  - URLs
  - speakers
- If ambiguous → return `null` for the field and add a short note to `Description`.

### B) Add role definitions
- **Organizer:** hosting unit/team/department or sender org responsible for event
- **Speaker:** person explicitly described as presenting/talking (trigger verbs required)
- **Contact:** signature person for questions (if schema has no `Contact`, keep in `Description`)

### C) Add date/time selection rules
- Choose date/time closest to explicit event markers:
  - “am/on”, “Uhr/time”, “Ort/location”, “Treffpunkt/meeting point”, “Beginn/start”
- De-prioritize:
  - dates embedded in URLs
  - deadlines unless clearly labeled as event date/time
- Handle `c.t.` / `s.t.`:
  - either store raw or set time null + note

### D) Add location validity checks
- If location is “TBA / will be announced / upon registration” → set `Location: null`

---

