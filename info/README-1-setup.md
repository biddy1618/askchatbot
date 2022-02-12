# Local set up

## Docker (version 20.10.12)

Pull images for Rasa and Rasa-SDK:
```bash
docker pull rasa/rasa:3.0.4-spacy-en
docker pull rasa/rasa-sdk:3.0.2
```

Create network for communicating between the services:
```bash
docker network create rasa
```

Build the images:
```bash
docker build -t rasa-actions -f rasa-actions.dockerfile .
docker build -t rasa .
```

Run the Rasa Actions server:
```bash
docker run --rm -it --net rasa --name rasa-actions rasa-actions
```

Run the Rasa Chatbot:
```bash
docker run --rm -it -p 127.0.0.1:5005:5005 --net rasa --name rasa rasa
```

## Or alternatively use Docker Compose (version 2.2.2)

Try setting the services up using `docker compose`:
```bash
docker compose build # if you already built images, omit
docker compose up
```

If you have already built the images, run the following to resume:
```bash
docker compose start
```

And to remove stopped containers and they are no longer needed, run following:
```bash
docker compose down
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