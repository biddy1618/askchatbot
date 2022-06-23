# Local set up

Instructions for linux-based machines.

## Docker Compose (version 2.2.2)

Launch the services up using `docker compose`:
```bash
docker compose build    # if you already built images, omit
docker compose up
```

FYI, the environment variables are set up in `.env` file.

If you have already built the images, run the following to resume:
```bash
docker compose start
```

And to remove stopped containers and they are no longer needed, run following:
```bash
docker compose down
```

__NOTE__: The endpoint for Elasticsearch service is set up by default at `https://dev.es.chat.ask.eduworks.com/` (as indicated at `.env` file). 
If you would like to run your own instance if ES, please, refer to file at "_./actions/es/deployment/README-1-es-deployment.md_" in this project.

To test the connection to ES, run the following in the python shell of __rasa-actions__ container:
```python
import requests
from requests.auth import HTTPBasicAuth 

requests.get('http://host.docker.internal:9200/', auth=HTTPBasicAuth('elastic', 'changeme')).json()
```

## Testing

Test the Rasa Actions server (should return the list of actions):
```bash
curl -X GET "localhost:5055/actions"
```

Test the Rasa Chatbot through RESTful API (should return response for message "Hi"):
```bash
curl -H "Content-Type: application/json" -X POST -d "{\"message\": \"Hi\", \"sender\": \"1\"}" "localhost:5005/webhooks/rest/webhook"
```

## Basic front end

### [Front-end](https://git.eduworks.us/ask-extension/askchatbot-widget)

Copy the project, change `VUE_APP_API_URL` to `http://127.0.0.1:5005/webhooks/rest/webhook`, and run the docker while exposing 8081 port:
```bash
docker build -t front-end
docker run -d -p 8081:8081 --name web-client front-end
```

### [Rasa-Chat](https://www.npmjs.com/package/@rasahq/rasa-chat) and Socket IO channel

Launch the server typing the following commands (python version 3.8):
```bash
python -m http.server -d ./web-client/socket-io/
```
You can access the simple web-client through `http://localhost:8000/`.

### Rest API

Launch the server typing the following commands (python version 3.8):
```bash
python -m http.server -d ./web-client/rest-api/
```
You can access the simple web-client through `http://localhost:8000/`.

More info at [github repo](https://github.com/RasaHQ/how-to-rasa/tree/main/video-10-connectors). Visit the [official github page](https://github.com/scalableminds/chatroom) of the project for more details. 

Make sure to run the Rasa chatbot with `--cors="*"` command inside the docker (the default). Additionally one can use `--debug` command for debugging:
```bash
rasa run --cors="*" # --debug
```

__NOTE__ - to test if CORS is enabled or not in our RESTful API (enabled by default):
```bash
SOURCE_URL=http://some-random-site
TARGET_URL=http://localhost:5005
curl -X OPTIONS -H "Origin: ${SOURCE_URL}" --head ${TARGET_URL}
```
It should output following:
```bash
Access-Control-Allow-Origin: ${SOURCE_URL} # http://some-random-site
```

## Rasa project structure details

```bash
📂 /path/to/project
┣━━ 📂 actions                      # actions
┃   ┣━━ 📂 static                   # static files
┃   ┃   ┣━━ 🔢 plant_matches.pkl    # data scraped from "plant diagnostic matrix"
┃   ┃   ┗━━ 🔢 plant_tree.pkl       # data scraped from "plant diagnostic matrix"
┃   ┣━━ 🐍 __init__.py              #
┃   ┣━━ 🐍 actions.py               # actions main module
┃   ┣━━ 🐍 helper.py                # helper functions for actions module
┃   ┣━━ 📄 plant_matching.ipynb     # EDA for scraped data
┃   ┗━━ 📄 requirements-action.txt  # modules used in actions module
┣━━ 📂 data                         # data for training Rasa chatbot
┃   ┣━━ 📂 lookup-tables            # lookup tables, i.e., synonyms
┃   ┃   ┣━━ 📄 plant-damage.yml     # 
┃   ┃   ┣━━ 📄 plant-disease.yml    #
┃   ┃   ┣━━ 📄 plant-name.yml       #
┃   ┃   ┣━━ 📄 plant-part.yml       #
┃   ┃   ┣━━ 📄 plant-pest.yml       #
┃   ┃   ┗━━ 📄 plant-type.yml       #
┃   ┣━━ 📄 nlu-request-plant-problem.yml    # training data for this intent
┃   ┣━━ 📄 nlu.yml                  # training data for minor intents
┃   ┣━━ 📄 rules.yml                # rule stories
┃   ┗━━ 📄 stories.yml              # general stories
┣━━ 📂 models                       # trained models
┣━━ 📂 tests                        # test folder
┃   ┗━━ 📄 test_stories.yml         # sample test
┣━━ 📄 config.yml                   # configuration file
┣━━ 📄 credentials.yml              # credentials file
┣━━ 📄 domain.yml                   # domain file
┣━━ 📄 endpoints.yml                # endpoints file
┣━━ 🐋 Dockerfile                   # dockerfile for rasa server
┣━━ 🐋 rasa-sdk.dockerfile          # dockerfile for rasa actions server
┣━━ 🐋 docker-compose.yml           # docker compose file
┣━━ 📄 index.html                   # HTML file for python web-client
┣━━ 📄 README.md                    # readme file
┣━━ 📄 endpoints.yml                # endpoints file
┗━━ 📄 requirements.txt             # requirements file
```

## Regarding Rasa X

Rasa X as of 04.01.2022 is not supported by Rasa 3.0.* - [source](https://rasa.com/docs/rasa-x/changelog/compatibility-matrix/). Support for [Rasa X for Rasa 3.0.*](https://forum.rasa.com/t/rasa-x-3-0/49700) is coming soon as authors say.

## `rasa-webchat` intergration

It is not compatible with `Rasa 3.0.*` since `rasa-webchat` requires `socket.io-client` be version of 3.1.2, but `Rasa 3.0.*` requires `python-socketio` (which `socketio` client) be later than 4.4 (and less than 6).