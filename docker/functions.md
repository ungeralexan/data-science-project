# Some imprtant commands to run
First get rid of the old containers:
docker compose down -v

Then build everything without cache to be sure 
docker compose build --no-cache


I run training once the model is created 
docker compose run --rm train


Chekc whetehr the artifcat lays on my mac
ls -l model

Then I start the API
docker compose up -d api

Then I open the docks
open http://localhost:8000/docs
