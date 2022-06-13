# Container for evaluating query ranking for Ask Extension Chatbot

Script for evaluating the relevancy of queries for Ask Extension Chatbot.

## Instructions on running experiments on MLFlow and Argo

1. Pull the project repo and make corresponding changes to project (in this case the project is https://git.eduworks.us/ask-extension/askchatbot)
2. Pull the jobs repo and update the `DESCRIPTION` correspondingly in `dev.yml` and `dev.yml.template` (in this case the jobs repo is at https://git.eduworks.us/ask-extension/jobs)
3. Execute the push commands in right order:
    1. Add, commit, and push the job repo
    2. Add, commit, and push the project repo
    3. Wait until the docker image is built for the project repo and deployment is successfull (in this case the project dockerize pipeline can be found at https://git.eduworks.us/ask-extension/askchatbot/-/pipelines and deployment can be checked by DEV server url - https://dev.chat.ask.eduworks.com/)
4. Then go to Argo at __ask.jobs.eduworks.com__ (log in with Eduworks SSI), select the corresponding workflow (in this case it is __chatbot-scoring__)
5. Delete that workflow (sounds not right, but it will trigger the workflow to run with latest `yml` files once again)
6. When workflow is rebuild again (green checkmark), go to __MLFlow__ at __https://ask.ml.eduworks.com__ (sign in with provided login and password, contact Dalila for details), and select the corresponding experiment (in this case __chatbot_scoring__)
7. You should be able to see latest metrics and stats corresponding to your experiment

__NOTE__: if one wants to run experiment on already deployed version of the project (i.e. miss the points _1_, _3.2_, _3.3_), then simply make sure that project is deployed and available on DEV server, and follow the pipeline omitting points _1_, _3.2_ and _3.3_.

## Running locally

Make sure that in `Dockerfile` the `RUN` command is executed without `--save` parameter:
```bash
# for testing locally
CMD ["python", "run_scoring.py"]
# for mlflow
# CMD ["python", "run_scoring.py", "--save"]
```

Also change the __RASA_URL__ in _docker-compose.yml_ file to:
```yml
...
RASA_URL: http://host.docker.internal:5005/webhooks/rest/webhook
...
```

Then run the container with following command:
```bash
docker compose up
```

__NOTE ON URL VALIDATION WHEN RANKING__:
The script strips the parameters of source links from ES database and uses simple string comparison.

## Adapting for MLFlow

Change the `RUN` command in the `Dockerfile` as follows:
```bash
# for testing locally
# CMD ["python", "run_scoring.py"]
# for mlflow
CMD ["python", "run_scoring.py", "--save"]
```

## Data validation

Details can be found at `scoring_data_elt.ipynb` notebook.