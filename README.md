# The Extension Bot

Repo for the Ask Extension chatbot component demonstration.

## Local set up and deployment

You can find the details for building the project locally in the following [`README-1-setup.md`](info/README-1-setup.md) file.

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

To see the details on ETL and EDA, refer to [`README-0-etl-data-sources.md](actions/es/README-0-etl-data-sources.md).

To read about the scoring pipeline, refer to [`README-scoring.md](scripts/scoring/README-scoring.md).