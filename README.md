# The Extension Bot

Repo for the Ask Extension chatbot component demonstration.

## Local set up and deployment

You can find the details for building the project locally in the following [`README-1-setup.md`](info/README-1-setup.md) file.


## Configuration Parameters
Configuration parameters are set in the [chat.js file](https://git.eduworks.us/ask-extension/askchatbot-widget/-/blob/prod/public/static/js/components/chat.js) of the frontend Widget and change the slot values in Rasa on page reload. 

The default parameters are shown below:
```json
{
    "search_size": 100,
    "cut_off": 0.4,
    "max_return_amount": 10,
    "ae_downweight": 0.8
}
```

### search_size
This is the number of returns prior to any kind of filtering based on client/state. Just raw results from Elastic Search prior to the filtering algorithms.

By default, this is set to 100. Meaning each query will return the top 100 results from Elastic Search. Then these will eventually get filtered down to up to the max_return_amount to show to the user.

In general, I don't see much of a reason for clients to play with this term. It's mostly used to give a good number of results prior to filtering while not being overly computationally expensive.

### cut_off: 
Cut off is a paramter that removes all sources with a score below your cut off threshold. 

By default, it's set to 0.4. This means that any score below 0.4 will not be shown to the user. 

If there are no scores above your threshold, the chatbot should indicate that it is incapable of finding a good result and direct you to your extension office for more help. 

### ae_downweight 
The source downweight parameter is designed to reduce the scores from AE Knowledge Base, i.e. giving higher priority to UC IPM resources.

The value should be set between 0 and 1
*  If  *ae_downweight* is set to *1*, no filtering is done based on source. The scores will be purely the cosine similarity value between the query/document embeddings.
* If *ae_downweight* is set to *0*, results from AE KB will be completely filtered out of the results.
* If *ae_downweight* is *between* 0 and 1, the scores from AE KB will be mulitiplied by the source_downweight. Effectively reducing their score since the downweight value is a fraction.

In general, `ae_downweight` should either be set to 0, 1, or a value close to 1 (say 0.9 or higher). If a `ae_downweight` term is small, the end result would just be completely filtering out the results with an additional computation. 

By default, this value is set to 0.8.

## Configuration Commands to play with 
This won't be enabled in production. However, if you want to play with configuration settings, you can change each field with the following commnds:
```
set parameter value
```
#### Examples
```
set max_return_amount 4
set ae_downweight 0.95
set search_size 90
set cut_off 0.4
```
## Things you can ask the bot

The bot can:

1. Find information based on pest-related question or request.
    1. Examples of requests:
    ```
    - Something is creating tunnels on my tomato plants. When I cut them open, I see yellowish worms or larvae with red or purple areas.
    ```

    ```
    - There are tiny flies hovering all over my fruit basket. How do I get rid of them?
    ```

    ```
    - I want to release lady bugs in my garden with the goal of keeping the aphid population to a minimum. Some guidance regarding purchase and implementation of the bugs.
    ```
2. Explain `Intergrated Pest Management`.
3. Connect to expert by showing the link to reach the expert.

## DEV server

The chatbot is available through `https://dev.chat.ask.eduworks.com/`.

## QA server

The chatbot is available through `https://qa.chat.ask.eduworks.com/`.

## Front-end

[Repository](https://git.eduworks.us/ask-extension/askchatbot-widget) for the front-end.

## Rasa project structure details

```bash
📂 /path/to/project
┣━━ 📂 actions                      # actions
┃   ┣━━ 📂 es                       # details on setting up of ES service
┃   ┃   ┣━━ 📂 deployment           # details on setting up of ES service
┃   ┃   ┣━━ 📄 .env                 # environment variables for docker compose
┃   ┃   ┣━━ 📄 docker-compose.yml               # docker compose file
┃   ┃   ┣━━ 🐍 es_chat_logging_index.ipynb      # scripts for creating chat logs index into ES
┃   ┃   ┣━━ 🐍 es_ingest_data.ipynb             # scripts for ingesting data into ES
┃   ┃   ┣━━ 📄 README-1-es-deployment.md        # guide on local set up of ES service
┃   ┃   ┗━━ 📄 README-2-es-ingesting-data.md    # guide on getting and ingesting data to ES service
┃   ┃   ┣━━ 📂 scripts              # additional scripts  
┃   ┃   ┃   ┣━━ 📂 events_sample    # sample of events logs for logging ETL
┃   ┃   ┃   ┃   ┗━━ ...             # ...
┃   ┃   ┃   ┣━━ 📂 hardcoded        # hardcoded question source and transformed files
┃   ┃   ┃   ┃   ┗━━ ...             # ...
┃   ┃   ┃   ┣━━ 📂 synonym_list     # synonym list source and transformed files
┃   ┃   ┃   ┃   ┗━━ ...             # ...
┃   ┃   ┃   ┣━━ 🐍 es_chat_logging.ipynb        # scripts (playground) for chat logging feature
┃   ┃   ┃   ┣━━ 🐍 es_etl.ipynb                 # EDA and ETL of data sources
┃   ┃   ┃   ┣━━ 🐍 es_hardcoded.ipynb           # scripts (playground) for hardcoded questions
┃   ┃   ┃   ┣━━ 🐍 es_playground.ipynb          # scripts (playground) for ES service calls
┃   ┃   ┃   ┗━━ 🐍 synonym_playground.md        # scripts (playground) for synonym replacement feature
┃   ┃   ┣━━ 🐍 __init__.py          #
┃   ┃   ┣━━ 🐍 config.py            # configuration file for the Rasa Actions service and ES
┃   ┃   ┣━━ 🐍 es.py                # implementation of ES retrieving functions for chatbot
┃   ┃   ┗━━ 📄 README-0-etl-data-sources.md     # information in EDA and ETL of the data sources
┃   ┣━━ 🐍 __init__.py              # 
┃   ┣━━ 🐍 actions_base.py          # base actions (like out-of-scope or greet)
┃   ┣━━ 🐍 actions_debug.py         # actions for debug purposes
┃   ┣━━ 🐍 actions_es.py            # actions for ES service retrieval of data
┃   ┣━━ 🐍 actions_main.py          # actions for add. feature like explain IPM or connect to expert
┃   ┣━━ 🐍 helper.py                # helper functions for actions module
┃   ┣━━ 📄 requirements-update.txt  # actions requirements file update for compatibility
┃   ┗━━ 📄 requirements.txt         # actions requirements file
┣━━ 📂 data                         # data for training Rasa chatbot
┃   ┗━━ ...
┣━━ 📂 models                       # trained models
┃   ┗━━ ...
┣━━ 📂 scripts/scoring              # scripts for scoring the chatbot
┃   ┣━━ 📂 data                     # data for scoring
┃   ┃   ┗━━ ...                     # ...
┃   ┣━━ 🐋 docker-compose.yml                   # docker compose file for automated scoring
┃   ┣━━ 🐋 Dockerfile                           # dockerfile for scoring
┃   ┣━━ 📄 README-scoring.md                    # guide on running the scoring script
┃   ┣━━ 📄 requirements-local.txt               # requirements file for local development
┃   ┣━━ 📄 requirements.txt                     # requirements file for scoring script
┃   ┣━━ 🐍 run_scoring.py                       # main script for running scoring
┃   ┣━━ 🐍 scoring_data_etl.ipynb               # ETL and EDA of test data for scoring
┃   ┣━━ 🐍 scoring_playground.ipynb             # scripts (playground) for scoring service
┣━━ 📂 web-client                   # alternative web-clients for debugging
┃   ┗━━ ...                         # ...
┣━━ 📄 .dockerignore                # docker ignore file
┣━━ 📄 .env                         # environment variables for docker compose file
┣━━ 📄 .gitignore                   # git ignore file
┣━━ 📄 .gitlab-ci.yml               # gitlab CI/CD configuration file
┣━━ 📄 config.yml                   # configuration file
┣━━ 📄 credentials.yml              # credentials file
┣━━ 📄 domain.yml                   # domain file
┣━━ 📄 endpoints.yml                # endpoints file
┣━━ 📄 .env                         # environment variables for docker compose
┣━━ 🐋 Dockerfile                   # dockerfile for rasa server
┣━━ 🐋 rasa-sdk.dockerfile          # dockerfile for rasa actions server
┣━━ 🐋 docker-compose.yml           # docker compose file
┣━━ 📄 README.md                    # readme file
┣━━ 📄 env-dev.sh                   # environment variables for local development
┣━━ 📄 requirements-local.txt       # requirements file local development (like jupyter)
┣━━ 📄 requirements-update.txt      # requirements file update for compatibility
┗━━ 📄 requirements.txt             # requirements file
```

## Auxillary

To see the details on ETL and EDA, refer to [README-0-etl-data-sources.md](actions/es/README-0-etl-data-sources.md).

To read about the scoring pipeline, refer to [README-scoring.md](scripts/scoring/README-scoring.md).