## What does supabase give us 

- The database (PostgreSQL):
This is where all  data lives. 
It’s a normal SQL database, so you can write and read data with SQL, just like in a school database course.

- APIs : They are automatically connected to the database.
You don’t have to build your own backend.Supabase automatically creates an API which means your app or dashboard can talk directly to the database safely.

- Auth : It also takes care of sign-up / login, and who is allowed to see what data (students only see their own data, etc.).
That’s called Row Level Security (RLS) every student’s view of the data is filtered automatically.

We dont host anything ourself, it is cloud based

## What does the API mean here and how to use it
We would use the API that supabase gives us to :
- Read data (“get me all events for next week”)
- Add data (“insert a new event”)
- Update data (“change the location of an event”)
- Delete data (“remove an old event”)


## Why it is practical to use it 
- You don’t need to set up your own database server.
- Everyone on your team can log in and see the same database through a web interface.
- You can built the dashboard later and connect it easily 
- It would also be secure enough for the university project or even a startup purpose


## What is docker 
Docker is a tool that helps you run programs anywhere, easily.

You make a little script that fetches emails and saves events.
It works on your laptop.
But your teammate tries it and says, “It doesn’t work on my computer — missing packages, wrong Python version…”.

Docker can fix that :
It puts your program and everything it needs (Python version, libraries, etc.) into a container — like a little box.
Now that box can run anywhere — on any computer, server, or cloud — and it will behave exactly the same.

## Why could it be usefull for the proyect :
We could build a programm that :
- Logs into student emails,
- Extracts events,
- Saves them into the Supabase database.
We could then put the program inside a Docker container and then later it could :
- Run it automatically on a server (every day, fetch new events).
- Share it with teammates (no “setup” problems).
- Stop/start it easily if something crashes.

Another possibility is to have multiple containers:
- one for the email-fetcher,
- one for maybe a small API,
- one for your dashboard — all running together neatly.


## How would a flow look like :
1. Your email-fetcher script runs inside a Docker container.
2. It reads new mails → turns them into event rows. (LLM probably)
3. It sends those rows to Supabase through Supabase’s API (HTTPS).
4. Supabase writes them into your Postgres database.

## How does docker work:
Once isntalled we get : Docker Desktop (a simple app you can click), and the Docker command-line (what most people use day-to-day).
But what would I then do with docker:
1. Define the environment your script needs (which language version, which libraries).
2. Build an image (a snapshot of that environment + your script).
3. Run a container from that image (that’s your script actually running).
4. When scheduled (via cron/Actions/etc.), that same container runs automatically.

## How could we make run it everyday:
We can rent a small virtual machine. There we can schedule tasks like run my script every morning or evening.  Perfect for tiny automations like your email-fetcher → Supabase job.

| Provider                          | Typical smallest option | Monthly cost | Notes                                      |
| --------------------------------- | ----------------------- | ------------ | ------------------------------------------ |
| **Google Cloud / AWS / Azure**    | free micro instance     | $0–$5        | academic programs often free credits       |
| **Hetzner Cloud**                 | 1 vCPU + 1 GB RAM       | ~€3–€4       | EU-based (often used by Tübingen projects) |
| **DigitalOcean / Linode / Vultr** | 1 vCPU + 1 GB RAM       | $5           | very beginner-friendly                     |
| **Local university server**       | sometimes free          | free         | ask IT if they host research projects      |


## Idea using AWS as virtual machine
We need to inform ourselves about the prices, but there are two options
- Lightsail (simplest UI) — great for “one small server that runs a daily job.”
- EC2 (standard AWS way) — a bit more knobs, but very common.

Our script  (inside Docker) runs on the server each morning (cron).
It fetches new mails → extracts events → calls Supabase’s API over HTTPS with your project URL + secret → inserts/updates rows.


## comparison uni cluster and cloud server
| Feature                    | University Cluster                              | Small Cloud VM                                         |
| -------------------------- | ----------------------------------------------- | ------------------------------------------------------ |
| **Who owns it**            | University / shared                             | You rent it personally                                 |
| **Access type**            | Through job scheduler (e.g. SLURM)              | Direct (you control everything)                        |
| **Always on?**             | Not really — jobs start/stop                    | Yes — 24/7 running                                     |
| **Main purpose**           | Heavy calculations, research workloads          | Hosting, automation, data fetching, dashboards         |
| **Good for your project?** | Not ideal — it’s not meant for daily automation | Perfect — small always-on jobs like your email fetcher |

