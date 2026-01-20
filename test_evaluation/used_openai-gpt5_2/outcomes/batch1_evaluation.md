# Batch 1 — Email 001 — Event Extraction Evaluation

Source files:
- `email_001.txt`
- `email_001_pred.json`

---

### Event 1

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
- The email describes a single combined “lecture and discussion” event on **14.11.2025, 14:00–17:30** at **Forum Scientiarum, Doblerstr. 33, Tübingen**, consistent with the predicted main event.


---

### Event 2

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
- The email specifies a lecture segment on **14.11.2025, 14:00–15:30** with the talk title “KI-Kunst und Kreativität” by **Harry Lehmann**, matching the predicted sub-event timing and speaker.


---

### Event 3

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
- The email specifies a discussion segment on **14.11.2025, 16:00–17:30** at the same venue with named discussants and a discussion lead, matching the predicted sub-event structure and timing.




# Batch 1 — Email 002 (Evaluation)



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
- The email specifies one “Tübinger Round Table Wissenschaftskommunikation & Public Engagement” event on **27.11.2025, 10–12 Uhr**, which matches the predicted start/end date and time.
- Interesting, it is correct but the email’s location line provides **room/building/street** details but does not explicitly include the city name; the prediction adds “Tübingen,” which is not stated in the location field as written.
- The email requests participants to register via a provided scheduling/registration link; therefore `Registration_Needed=true` with a `Registration_URL` is consistent.
- No online meeting link is provided in the email, so `Meeting_URL=null` is appropriate.



# Batch 1 — Email 003 (Evaluation)
No email found as randomized



# Batch 1 — Email 004 (Evaluation)
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
- The email clearly states an **intercultural training** taking place on **04 December** from **10:00–15:00**, which matches the predicted date and time window.  
- The email includes a registration form link for the Buddy program; using it as `Registration_URL` together with `Registration_Needed=true` is consistent with the email’s registration instruction.  
- No online meeting link is provided; `Meeting_URL=null` is appropriate.  
- The email attributes the invitation to the **T-IES Team** and does not name a speaker; the prediction’s organizer/speaker fields align with that.



# Batch 1 — Email 005 (Evaluation)
**Field Checks**
- Title: Correct
- Date & Time: Incorrect
- Location: Incorrect
- Registration Logic: Correct
- Meeting_URL: Correct
- URL Separation: Incorrect
- Speaker vs Organizer: Correct
- Multi-Event Handling: Incorrect

**Event Score:** 4 / 8

**Notes**
- The email announces “Sonnenenergie & KI” on **Sa., 15.11.2025** starting **14:00** with a detailed agenda (tour, two talks, dinner). The prediction correctly captures the date and start time but **adds an end time** not specified in the email.
- The event content spans **multiple agenda components/venues** (Solarthermie-Park Au plus a named dinner location). A single location entry limited to only one place is not fully supported.
- The email provides a “Details und Anmeldung” link; setting `Registration_Needed=true` with a registration link is consistent. However, the prediction duplicates the same PDF link in both `URL` and `Registration_URL`, violating URL separation rules.
- Named presenters in the email match the prediction’s speaker list; the organizer attribution to the university computer science/cognitive science context is consistent with the sender/signature context.
