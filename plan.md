# Personalized Event Recommendation App – University of Tübingen

## 1) Problem Framing

**Goal:** Recommend upcoming campus events that each student is likely to care about.

**Setting:** Daily “Rundmail” events (German/English) pulled from Horde → parsed into structured “event” objects.

**Cold start:** Interests from onboarding quiz.

**Learning loop:** Clicks, saves, hides, RSVP/attended → continuous model updates.

---

## 2) Data Pipeline (MVP → Robust)

### Ingest
- IMAP fetch (Horde) → dedupe by Message-ID + near-duplicate hashing (minhash).
- Store raw MIME + parsed text/HTML.

### Parse & Normalize
- Extract: title, description, date/time, location, organizer, links, cost, tags (if any).
- Normalize times to **Europe/Berlin**, handle ranges & multi-day.
- Detect language (de/en) → translate to a pivot or use multilingual models.

### Clean & Enrich
- Rule patterns + small LLM pass to fix: missing titles, weird line breaks.
- **NER** for orgs/locations (spaCy `de_core_news_lg` + `en_core_web_lg`).
- **Topic tags:** zero-shot multi-label (e.g., “career”, “research talk”, “sports”, “culture”, “parties”, “volunteering”, “admin”, “workshops”, “student groups”).
- **Embeddings:** multilingual sentence embeddings (e.g., `all-MiniLM-L12-v2` or `Instructor-xl`) for title/abstract + separate “time” and “place” features.
- Push to a vector store (FAISS/pgvector) + relational store for metadata.

---

## 3) User Modeling

### Onboarding Quiz → Preference Vector
- Ask for: fields (econ, cs, psych…), formats (workshop/party/lecture), days/times, budget, campus locations, languages.
- Convert to:
  - (a) Term weights (keywords/tags)
  - (b) Embedding centroid from exemplar prompts (“I like career fairs, data science talks, hiking club” → embed).

### Behavioral Updates
- Actions: view, click, save, hide, “not interested”, “I went”.
- Maintain two profiles:
  - **Content profile vector:** embedding centroid of liked events + quiz.
  - **Preference scalars:** day-of-week, time-of-day, language, location radius, organizer affinity.
- Decay older signals (exponential).

---

## 4) Recommender Methodology (Hybrid, Stepwise)

### MVP (week 1–2): Content-Based + Rules
- Candidate gen: events within upcoming 14–21 days, not expired, not duplicate, fits availability.
- Score = cosine(user_vec, event_vec).
- Re-rank with a simple linear score:
0.55 * similarity + 0.15 * recency_boost + 0.10 * organizer_affinity + 0.10 * tag_overlap + 0.10 * schedule_fit


- Add hard filters: language (opt-in), max distance, conflicts with user calendar (optional integration later).

### V2 (week 3–4): Add Collaborative & Popularity
- Implicit MF (ALS via `implicit` library) or **LightFM** with content features.
- Popularity priors: CTR, saves, RSVP proxy.
- Hybrid blend: `α * CF_score + (1-α) * content_score`.
- Cold-start users → quiz-only content model; cold-start items → content + global popularity.

### V3 (week 5+): Contextual Bandits for Explore/Exploit
- Per-slot re-ranking with LinUCB or Thompson Sampling using features:
  - similarity, freshness, hour-match, weekday-match, distance, popularity.
- Small exploration budget (e.g., 10–15%) to learn long-tail interests.

### V4 (optional): Learning-to-Rank
- Train XGBoost/LGBM ranker on labeled pairs (shown vs clicked/saved) with features above.
- Optimize NDCG@k.

---

## 5) Event Understanding (Taxonomy + Tagging)

- Define a controlled taxonomy (≤20 tags):  
  `{Career, Research, Entrepreneurship, Sports, Music, Culture, Party, Department, Admin/Deadlines, Volunteering, Language Tandem, Workshops (Tech/Soft), Student Clubs, International, Family, Well-being, …}`

- Assign tags via:
  - Zero-shot classifier (multilingual)
  - Weak supervision (Snorkel): keyword lists per tag → label functions → model.
- Keep multi-label; store per-tag confidence.

---

## 6) Ranking Features (Examples)

- Content similarity (title, abstract)
- Tag overlap Jaccard
- Recency and lead time (events too soon/too far → penalty)
- Temporal fit: user’s preferred days/hours
- Location proximity (distance to user’s campus)
- Organizer affinity (dept, student council, clubs)
- Popularity (global CTR, saves, RSVPs)
- Diversity penalty to avoid near-duplicates in top-k

---

## 7) Feedback Loop & Evaluation

### Offline
- Historical replay: split by time.
- Metrics: Precision@k, Recall@k, NDCG@k, MAP, coverage, catalog diversity, serendipity.

### Online
- CTR, save-rate, hide-rate, RSVP-rate, dwell time.
- A/B: baseline content vs hybrid vs bandit.
- Guardrail: complaint rate (irrelevance), latency p95.

---

## 8) Architecture (Simple & Scalable)

- **Backend:** FastAPI (Python)
- **Store:** Postgres (events/users/feedback), pgvector or FAISS for embeddings; Redis for candidate cache.
- **Workers:** Celery/Prefect for IMAP fetch → parse → enrich → index (hourly)
- **Models:** Hugging Face sentence transformers; implicit/LightFM; scikit-learn/XGBoost for LTR.
- **Telemetry:** OpenTelemetry + Prometheus; dashboards in Grafana.

---

## 9) UI/UX (What Matters)

- **Onboarding quiz:** pills/toggles + free-text “tell us what you like”.
- **Home feed:** cards with title, short blurb, date/time, location map pin, tags, “Save”, “Hide”, “Share”, “I’m in”.
- **Controls:** filters (dates, categories, campus), “surprise me”.
- **Explanations:** “Because you like Data Science & Workshops; organizer: MWTI”.
- **Calendar export** (.ics) and reminder notifications.
- **Feedback prompts** after events: “Was this relevant?”

---

## 10) Data Schema (Minimal)

**events**  
`id, source_id, title, description, start_dt, end_dt, tz, location_text, lat, lon, language, organizer, tags[], embed_vector, created_at, updated_at`

**users**  
`id, language_pref, campus, max_distance_km, quiz_tags[], quiz_embed_vector, time_prefs_json`

**interactions**  
`user_id, event_id, action {view, click, save, hide, rsvp, attended}, ts, context (position, device)`

**organizers**  
`name, type, affinity_score_per_user (materialized view)`

---

## 11) Privacy & Compliance (GDPR-Safe)

- Don’t store personal email content; only store **events extracted from Rundmails**.
- Clear consent for behavioral tracking; per-user data export/delete.
- Pseudonymize user IDs; log aggregation after 90 days.

---

## 12) Milestones (Tight, Realistic)

### M1 – 1 week: MVP Ingest & Basic Recs
- IMAP fetch → parse → structure.
- Multilingual embeddings + cosine ranking.
- Minimal React/Tailwind UI with onboarding + top-k list.
- Offline eval on small labeled set.

### M2 – 2–3 weeks: Hybrid Recs + Feedback
- Implicit MF/LightFM + popularity priors.
- Feedback events wired (click/save/hide).
- Basic A/B switch + metrics pipeline.

### M3 – 4–5 weeks: Bandits + Re-Ranker
- Contextual bandit re-ranking in delivery layer.
- Diversity constraints; explanations.

### M4 – Polish
- Calendar export, reminders, organizer pages, admin tag editor.
- Data retention & privacy features.

---

## 13) Risk Table & Mitigations

| Risk | Mitigation |
|------|-------------|
| Messy emails | Build regex + LLM fallback summarizer (“extract title/date/place”) |
| Multilingual noise | Use multilingual embeddings; optional translation |
| Sparse feedback | Start with popularity + content; add bandit exploration |
| Cold start users | Strong onboarding; sample “like” examples |
| Time quality | Strict validation; drop events without reliable datetime |

---

## 14) Tech Stack Choices (Pragmatic)

- **Python 3.11**, FastAPI, Poetry  
- **Database:** Postgres + pgvector; FAISS if needed  
- **ML:** `sentence-transformers` (multilingual-MiniLM or Instructor), `implicit`/LightFM, XGBoost for LTR, Vowpal Wabbit or LinUCB for bandits  
- **NLP:** spaCy (de/en), dateparser, Duckling  
- **Frontend:** React + Tailwind + shadcn/ui  
- **Pipelines:** Prefect; Docker for deploy  

---

## 15) What to Implement First (Today)

1. Define the **event taxonomy** (≤20 tags) and keyword lists.  
2. Build the **email → event extractor** (title, date/time, location, description).  
3. Index 2–3 weeks of historical Rundmails → embeddings.  
4. Build a **cosine-similarity recommender** and a minimal UI with onboarding.  
5. Log interactions and compute **Precision@10 / NDCG@10** on a hand-labeled dev set.


