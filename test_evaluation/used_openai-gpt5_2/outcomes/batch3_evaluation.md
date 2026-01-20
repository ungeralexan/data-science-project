# Batch 3 — Email 011 (Evaluation)

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
- The email announces a College of Fellows event within the “CoF Lecture Series” on 03.12.2025 at 18:30 at Villa Köstlin (Rümelinstr. 27, 72070 Tübingen). The predicted main-series entry is consistent with this framing and details. fileciteturn9file1 fileciteturn9file0

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
- The email explicitly names the lecture title and presenter (“Cultural and Creative Product Design in Museums” with Prof. Weijun Hu) on 03.12.2025 at 18:30 at Villa Köstlin; the predicted sub-event matches. fileciteturn9file1 fileciteturn9file0
- The sub-event is properly linked to a corresponding main event via a shared `Main_Event_Temp_Key`. fileciteturn9file0

---



# Batch 3 — Email 012 (Evaluation)

### Event 1

**Field Checks**
- Title: Correct
- Date & Time: Incorrect
- Location: Correct
- Registration Logic: Incorrect
- Meeting_URL: Correct
- URL Separation: Incorrect
- Speaker vs Organizer: Correct
- Multi-Event Handling: Incorrect

**Event Score:** 4 / 8

**Notes**
- The email describes a program consisting of **three separate weekend modules** (with distinct date ranges in March, April, and June 2026). Representing the whole program as one continuous event from 20.03.2026 to 14.06.2026 merges distinct events and is therefore not supported by the email’s structure.
- The email provides a general information link (“Find more information”) and does not explicitly label it as an application/registration link; using it as `Registration_URL` is not directly supported. In addition, the same link is duplicated in both `URL` and `Registration_URL`, violating URL separation rules.
- Organizer attribution to the “Startup Center” and absence of a speaker are consistent with the email.

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
- The email explicitly announces an **online Q&A session** on **Friday, 12.12.2025, 12:30–13:00** “via Zoom”, matching the predicted date/time and online format.
- The email does not include a Zoom meeting link; therefore `Meeting_URL=null` is appropriate.
- The sub-event is correctly linked to a corresponding main event via a shared `Main_Event_Temp_Key`.






# Batch 3 — Email 013 (Evaluation)



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
- The prediction’s sub-event matches the email’s online presentation segment on 11.12.2025 from 12:15–13:00 and correctly places the Zoom access link in `Meeting_URL`.
- The sub-event is properly linked to a corresponding main event via a shared `Main_Event_Temp_Key`.



# Batch 3 — Email 014 (Evaluation)
No email found as randomized




# Batch 3 — Email 015 (Evaluation)

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
- The email announces one “Startup Center Meetup” on **Wednesday, 10.12.2025** from **5:30 pm to 7:30 pm** at **Startup Center, Ob dem Himmelreich 7, 72074 Tübingen**, matching the prediction’s date/time and location. fileciteturn12file1
- The email explicitly asks recipients to register via a provided link; `Registration_Needed=true` and the `Registration_URL` are consistent, and the general Startup Center website is appropriately placed in `URL` (distinct from the registration link). fileciteturn12file1 fileciteturn12file0
- No online meeting link is provided; `Meeting_URL=null` is appropriate. fileciteturn12file1
