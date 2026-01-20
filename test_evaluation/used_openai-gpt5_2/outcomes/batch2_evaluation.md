# Batch 2 — Email 001 (Evaluation)

### Event 1

**Field Checks**
- Title: Correct
- Date & Time: Correct
- Location: Incorrect
- Registration Logic: Correct
- Meeting_URL: Correct
- URL Separation: Correct
- Speaker vs Organizer: Correct
- Multi-Event Handling: Correct

**Event Score:** 7 / 8

**Notes**
- The email describes a two-day “SEA:start” workshop on **Thu 04.12.2025** and **Fri 05.12.2025**, each **09:00–16:30**, which matches the predicted start/end dates and times.
- The email states the place as “Seminarraum, Startup Center” and separately provides a postal address in the contact section; the prediction combines these into a full address (and adds a country), which is not explicitly stated as the event location line.

---

### Event 2

**Field Checks**
- Title: Correct
- Date & Time: Correct
- Location: Incorrect
- Registration Logic: Correct
- Meeting_URL: Correct
- URL Separation: Correct
- Speaker vs Organizer: Correct
- Multi-Event Handling: Correct

**Event Score:** 7 / 8

**Notes**
- “SEA:start” Day 1 on **04.12.2025, 09:00–16:30** matches the email’s stated first day schedule.
- Location is over-specified for the same reason as Event 1 (the email does not explicitly tie the full street address to the workshop room line).

---

### Event 3

**Field Checks**
- Title: Correct
- Date & Time: Correct
- Location: Incorrect
- Registration Logic: Correct
- Meeting_URL: Correct
- URL Separation: Correct
- Speaker vs Organizer: Correct
- Multi-Event Handling: Correct

**Event Score:** 7 / 8

**Notes**
- “SEA:start” Day 2 on **05.12.2025, 09:00–16:30** matches the email’s stated second day schedule.
- Location is over-specified for the same reason as Event 1.

---

### Event 4

**Field Checks**
- Title: Correct
- Date & Time: Correct
- Location: Incorrect
- Registration Logic: Correct
- Meeting_URL: Correct
- URL Separation: Correct
- Speaker vs Organizer: Correct
- Multi-Event Handling: Correct

**Event Score:** 7 / 8

**Notes**
- Location is over-specified in the same way as the SEA:start events (full address and country not explicitly stated as the event’s place line).

---

### Event 5

**Field Checks**
- Title: Correct
- Date & Time: Correct
- Location: Incorrect
- Registration Logic: Correct
- Meeting_URL: Correct
- URL Separation: Correct
- Speaker vs Organizer: Correct
- Multi-Event Handling: Correct

**Event Score:** 7 / 8

**Notes**

- Location is over-specified as described above.

---

### Event 6

**Field Checks**
- Title: Correct
- Date & Time: Correct
- Location: Incorrect
- Registration Logic: Correct
- Meeting_URL: Correct
- URL Separation: Correct
- Speaker vs Organizer: Correct
- Multi-Event Handling: Correct

**Event Score:** 7 / 8

**Notes**
- Location is over-specified as described above.

---

### Event 7

**Field Checks**
- Title: Correct
- Date & Time: Correct
- Location: Incorrect
- Registration Logic: Correct
- Meeting_URL: Correct
- URL Separation: Correct
- Speaker vs Organizer: Correct
- Multi-Event Handling: Correct

**Event Score:** 7 / 8

**Notes**
- “Your Research Canvas” on **Fri 30.01.2026, 14:00–18:00** matches the email’s stated date and time.
- Location is over-specified (full street address and country not explicitly stated as the event’s place line).



# Batch 2 — Email 007 (Evaluation)


**Field Checks**
- Title: Correct
- Date & Time: Correct
- Location: Correct
- Registration Logic: Correct
- Meeting_URL: Correct
- URL Separation: Correct
- Speaker vs Organizer: Correct
- Multi-Event Handling: Correct

**Event Score:** 8 / 8

**Notes**
- The email announces a single “AI Companion Meetup” on **10.12.2025, 17:00–18:30**, matching the predicted date and time window. 
- Registration is explicitly required (sign-up by a deadline via email), so `Registration_Needed=true` is consistent even without a registration URL. 
- No online meeting link is provided; `Meeting_URL=null` is appropriate. 



# Batch 2 — Email 008 (Evaluation)


**Field Checks**
- Title: Correct
- Date & Time: Correct
- Location: Correct
- Registration Logic: Correct
- Meeting_URL: Correct
- URL Separation: Correct
- Speaker vs Organizer: Correct
- Multi-Event Handling: Correct

**Event Score:** 8 / 8

**Notes**
- The email announces a single workshop on **Friday, 28.11.2025** from **09:00–12:45 (s.t.)**, matching the predicted date and time window.
- The email references “Anmeldung” and provides an event page link, so `Registration_Needed=true` is consistent. No online meeting link is given, so `Meeting_URL=null` is appropriate.
- Names in the signature are staff contacts, not described as speakers; `Speaker=null` and `Organizer=Zentrale Studienberatung` align with the email.



# Batch 1 — Email 0009 (Evaluation)
No email found as randomized





# Batch 2 — Email 010 (Evaluation)

### Event 1

**Field Checks**
- Title: Correct
- Date & Time: Correct
- Location: Incorrect
- Registration Logic: Correct
- Meeting_URL: Correct
- URL Separation: Correct
- Speaker vs Organizer: Correct
- Multi-Event Handling: Correct

**Event Score:** 7 / 8

**Notes**
- The email describes one “Learning Lab: Exit Loneliness / Exit Einsamkeit” session on **22.11.2025, 17:00–19:45**, which matches the predicted date and time window.
- The email’s “When & Where” line gives the venue and street plus floor, but does not state a city/country for the event location; the prediction over-specifies by adding “Tübingen, Germany”.
- The email explicitly states **no registration required** (“Ohne Anmeldung / just drop by”), so `Registration_Needed=false` with no registration link is consistent.


---


