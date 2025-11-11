# How to install supabase on docker
The code : 
npm install -g supabase
supabase --version

**Problem** 
What if Node.js is not installed yet. You have to install it. Hence
1. go to  https://nodejs.org
2. click the “LTS” (Long Term Support) version
3. we need to download it for mac in my case
4. Then we open it -> follow the installer -> finish (which might needs the password)

This is just a javascript runtime outside the browser. I need it as The Supabase CLI (Command Line Interface) is written in Node.js.
with this I can:
- download the correct Docker containers
- manage them 
- give me handy commands like supabase start or supabase db push

**The installation can be verified by**
node -v
npm -v


## YOu dont have to do this when having docker compose at the server
On your laptop, get things working with supabase start and commit the generated config (or export a compose file—happy to draft one).
Copy your repo to the server: git clone ... /opt/your-project
Then on the server : cd /opt/your-project
docker compose up -d

This brings up Postgres, Auth, REST, Realtime, and Studio—all as containers.


# How does docker work
You have an image: a snapshot (code + Python + libraries).
Then a container a running instance of an image.
We dont install the libraries on the server, we bake them inside the image. Supabase runs in its own containers, Your scripts connect to it over HTTP like any normal API/DB.

For our proyect what about doing two images:
etl_scraper → reads emails, creates events.csv, inserts to DB.
matcher → reads profiles+events, creates matches, writes to DB.

**In each image we then define the libraries**:
We often have kind of an requierements.txt that entails :
supabase
pandas
python-dotenv
beautifulsoup4


## Idea how to proceed could be 
1. You develop everything locally (scripts, Dockerfiles, configs, Supabase setup).
2. You push your project to GitHub.
3. On the university VM:
- We install docker and docker compose once
- I clone my github repo into a folder
- Run docker compose up -d -> everything starts


## Dockerfile does what you tell him
It starts from the base system, installs certain lirbrairies, copy in my code and when I run execute this command.


The file : 
# Start from a base image with Python preinstalled
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependency list and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your script(s)
COPY . .

# Command that runs when the container starts
CMD ["python", "scrape_emails_to_csv.py"]


-> In the end you run: docker build -t etl_scraper .
Docker then reads that file, follows the instructions, and creates a Docker image (which is a self contained enviroment with python + my libraries and my code)


Each Dockerfile creates one image.
In my case:
1 Dockerfile for the ETL/scraper script
1 Dockerfile for the Matcher/LLM script
This is normal as each skript normally entails one image

## Docker compose
Is the thing that makes several containers run together. 
In my case it would be this : 
- Supabase stack (database, auth, UI)
- Your two scripts
- (Maybe later a FastAPI backend or a cron scheduler)

You then describe all in the docker-compose.yml; This is like an orquestral score. That tells docker how to start everything.

It could all loook like this together : 
version: "3.9"
services:
  supabase:
    # we actually let 'supabase start' handle this locally, but you could run it here later
    image: supabase/postgres:15
    ports:
      - "5432:5432"

  etl_scraper:
    build: ./etl_scraper
    volumes:
      - ./data:/app/data
    environment:
      SUPABASE_URL: "http://host.docker.internal:54321"
      SUPABASE_SERVICE_KEY: "${SUPABASE_SERVICE_KEY}"

  matcher:
    build: ./matcher
    volumes:
      - ./data:/app/data
    environment:
      SUPABASE_URL: "http://host.docker.internal:54321"
      SUPABASE_SERVICE_KEY: "${SUPABASE_SERVICE_KEY}"


In the end I run this : docker compose up -d
This would then rebuild the yaml file
Builds the images (using dockerfiles)
Starts each container with the right enviroments variables 


# What is then left to be done in the virtual machine:
# 1. install docker & compose (once)
sudo apt update
sudo apt install docker.io docker-compose-plugin -y
sudo systemctl enable --now docker

# 2. create a folder for your project
mkdir /opt/your-project && cd /opt/your-project

# 3. clone your repo
git clone https://github.com/yourname/yourrepo.git .

In the repo I should have:
etl_scraper/Dockerfile
matcher/Dockerfile
docker-compose.yml
data/ (optional)

In the end then what I do is : 
# 4. build the images (only first time)
docker compose build

# 5. run the containers
docker compose up -d


This and then my scirpts and supabase will start 