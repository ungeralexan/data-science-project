# Why would we need a database
We have multiple evolving and updating pieces of data that each of us might need 

## What we will have to do 
Database can be super beneficial to query, filter, sort, deduplicate, and join information quickly.

## What to use 
PostgreSQ as database engine.
This we could run on the laptop, server or even docker
Then there is **supabase** : a hosted platform built on PostgreSQL.
Here we get 
- A managed Postgres (no server setup),
- A REST & realtime API auto-generated from your tables
- Auth, row-level security, storage buckets, dashboards,
- Backups, UI to edit data, SQL editor.


## Where and how could we store data 
events → title, description, start_time, end_time, location, url, organizer_id
organizers → name, email_domain
students → email, name
interests + join tables (student_interests, optional event_interests)

**Optional interesting for storage could be**
Raw email bodies, attachments, ICS files → store in a bucket (Supabase Storage or S3/MinIO) and keep a URL/pointer in events.


## What about supabase storage and costs 
The free plan includes: ~500 MB Postgres, 1 GB file storage, 5 GB egress, 50k MAUs, unlimited API requests, 2 active projects, and free projects pause after 7 days of inactivity.

A database and table could be created the following way :
```sql

create table events (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  description text,
  organizer text,
  start_time timestamptz not null,
  end_time timestamptz,
  location text,
  url text,
  source_message_id text unique, -- helps dedupe
  created_at timestamptz not null default now()
);

create index on events (start_time);
```
How would i get now the rows in there, as I just only created the table

## Possibilities

1. Script pushes rows
- Your ingestion script (Python/Node) parses emails → builds rows → upserts into events using the Supabase client.
- It can run on a uni server, a laptop, or a cron in the cloud.

2. I do an CSV import
- Teammates drop a CSV into Supabase’s Table editor → Import data (great for a first batch).
- But you need to switch to A for automation, the above could be tried though

## What can you do then in the databse
- You could filter for the next 30 upcoming events 
- Or a certain keyword search could be implemented in there 

## Connect to the dashboard is possible
Use @supabase/supabase-js. Turn on Row Level Security (RLS) and write policies to control who sees what.

Could look like this in python

```python
// npm i @supabase/supabase-js
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(import.meta.env.VITE_SUPABASE_URL, import.meta.env.VITE_SUPABASE_ANON_KEY)

export async function getUpcomingEvents() {
  const { data, error } = await supabase
    .from('events')
    .select('*')
    .gte('start_time', new Date().toISOString())
    .order('start_time', { ascending: true })
    .limit(50)
  if (error) throw error
  return data
}
```

**The second option entails**
A small backend api that might give you more control. Build a tiny FastAPI/Express service that reads from Supabase (or connects to Postgres directly) and exposes endpoints like /students/:id/next-events.

## Trying supabase
Created a table to check whether it works
table_events (unrestricted)
**what does it mean**
- You created a table called test_events, ✅
- And currently it has no Row Level Security (RLS) turned on — i.e. “unrestricted” access. It just means anyone with your API key can read/write to that table



# Test Application
## What is being done :

You run a script that goes like :
```python
{"title": "AI Meetup", "source_message_id": "<msg-201@example>"}
```
this becomes one row in the test events.
Inside the supabase these are stored as mutual recors. It moroever gives them an additional ID and puts an created_at file.
In the created database: multiple people and programs can write to it at once and you can enforce rules. Its is practically a real onllien database that you can both write to (upsert) which means update and insert. Moreover also read from using python. 


# Which kind of dashbaord could be created 
## First option : Fast MVP (no backend): React/Next.js + Supabase JS
This would be the easiest way to ship something nice-looking quickly. No server to manage.
It connects as the browser uses Supabase JS client with your anon key. You then protect data using Row Level Security. 

## Second option : The ultra quick internal tool: Streamlit + supabase-py
This could be seen as a working data app today for classmates. 
Python uses the supabase-py client with your anon key (or service role for server side). We could deploy it using Streamlit Community Cloud, or run on a uni VM.
It is insanely fast to build, great for demos & internal use. But it is not as flexible for polished public site. 
