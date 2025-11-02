# 📊 Data Science Project: Event Recommendation Schema Ideas

This document outlines the proposed database schema for the personalized event recommendation app, separating data into two main tables: **Events** (the items to be recommended) and **Student_Profiles** (the users).

## 1. Event Table (`events`)
- event_id; Primary Key;  Unique identifier for the event.

- title; Text; Main event title

- description; Text; short event description

- time; Timestamp with Timezone; Crucial for the Freshness time-decay score.

- location; Text; Where the event takes place.

- event_url; Text; Link to more information/registration;

- contact_email, Text, Email of the person in charge.

---

## 2. Student Profile Table (`student_profiles`)

**Purpose:** To store student data and preferences collected via the onboarding questionnaire. This data is used to generate the profile vector for matching.

- student_id; Primary Key; Unique student identifier.

- study_program; Text; Broad filter for relevance (e.g., "Computer Science," "Mechanical Engineering").;

- explicit_interests; Text Array; List of selected topics (e.g., ["Machine Learning," "Entrepreneurship," "Climate Change"]).

- interest_text_data; Text;  A longer-form text box for a student to write specific interests—this is excellent for Text Construction and Embedding.

- preferred_event_type; Text Array; Explicit preferences (e.g., ["Workshop," "Talk," "Career Fair"]).

- feedback_likes; Text Array; List of event_ids the student has "Liked" (for future model training/refinement).