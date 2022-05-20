# Container for evaluating query ranking for Ask Extension Chatbot

Script for evaluating the relevancy of queries for Ask Extension Chatbot.

## Instructions on running experiments on MLFlow and Argo

1. Pull the project repo and make corresponding changes to project (in this case the project is https://git.eduworks.us/ask-extension/askchatbot)
2. Pull the jobs repo and update the `DESCRIPTION` correspondingly in `dev.yml` and `dev.yml.template` (in this case the jobs repo is at https://git.eduworks.us/ask-extension/jobs)
3. Execute the push commands in right order:
    1. Add, commit, and push the job repo
    2. Add, commit, and push the project repo
    3. Wait until the docker image is built for the project repo (in this case the project dockerize pipeline can be found at https://git.eduworks.us/ask-extension/askchatbot/-/pipelines)
4. Then go to Argo at __ask.jobs.eduworks.com__ (log in with Eduworks SSI), select the corresponding workflow (in this case it is __chatbot-scoring__)
5. Delete that workflow (sounds not right, but it will trigger the workflow to run with latest `yml` files once again)
6. When workflow is rebuild again (green checkmark), go to __MLFlow__ at __https://ask.ml.eduworks.com__ (sign in with provided login and password, contact Dalila for details), and select the corresponding experiment (in this case __chatbot_scoring__)
7. You should be able to see latest metrics and stats corresponding to your experiment

## Running

Run the container with following command:
```bash
docker compose up
```

__NOTE ON URL VALIDATION WHEN RANKING__:
The script strips the parameters of source links from ES database and uses simple string comparison.

## Adapting for MLFlow

Change the necessary lines correspoing to `logger.print(...)`.

## Data format

Data should be available in pickle format. Data transformation script is available under `scoring_data_etl.ipynb` notebook.

It consists of the following columns:

| Question         | ExpectedAnswer                  | URL                                   | Source                         |
|------------------|---------------------------------|---------------------------------------|--------------------------------|
| Questions itself | Reference answer(s) from UC IPM | Link(s) to the problem in UC IPM site | Question source (UC IPM or AE) |

__Notes__:
* If there are several expected answer references they are separated by `\n` (new line) character
* Same applies to URLS - if there are several URLs they are separated by `\n` (new line) character
* All URLs are striped from optional parameters (`?`)
* Line crawled can have two varibles - `Y` and `N`
* Alternative link can be null