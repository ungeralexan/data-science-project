# data-science-project
Data Science Project Repository for the Tübingen event planner. Team : Veja, Maurice, Alex

## The idea 
Turn unstructured university mailing-list messages into a personalized feed of **relevant events** (talks, workshops, deadlines, career fairs) with a clean UI.

## Problem and motivation
University mails are noisy often along and easy to overlook. Students miss events that match their programm and interests. We extract event info and for your profile so you only see what matters.

## How would we approach
Use IMAP (read-only) to fetch from our mail folders, Veja here actually already wrote a script that can store the respective mail files each in a text file. 
***Question: How do we get the relevant from the mails-text files***:
Parse them out : dates/times/locations/orgs could be parsed out with spaCy and a robust data parser. 
Problem: What if tehre are several dates? how do we know at whcih date is actual event. 
***Question***: What is the relevant infomation we want to get out: Name, Organizer, Time, short description? And maybe combine in with a calendar in the app where you could insert the events.
***idea*** What about using regular expressions to parse out important info, but maybe we get to much information that at the same time is biased.


## How do we find the relevant events and how do we match?
Idea would be using NLP. We looked maybe there is some kind of BERT model that encodes the words in vectors and we then match the words over cosine similairty, but we would have to take a closer look into that. 


## We then could either build a dashboard or an APP
There we use Thin FastAPI backend (ingest, extract, search). 
An app could then be created with for instance streamlit. 
- Profile setup (study program, interests).
- “Upcoming for you” list, calendar view, filters.
- Export .ics for each event (nice touch!).
- (maybe even feedback buttons that tell how interested the person is (or too much?))

## Where would we store everything
- SQLite/Postgres ?

