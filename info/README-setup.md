# Local set up

## Docker (version 20.10.12)

Pull images for Rasa and Rasa-SDK:
```
docker pull rasa/rasa:3.0.4-spacy-en
docker pull rasa/rasa-sdk:3.0.2
```

Create network for communicating between the services:
```
docker network create rasa
```

Run the actions server with volume for actions:
```
docker build -t rasa-sdk -f rasa-sdk.dockerfile .
docker run --rm -it -v $(pwd)/actions:/app/actions --net rasa --name action-server rasa-sdk
```

Run the Rasa Chatbot:
```
docker run --rm -it -p 0.0.0.0:5005:5005 -v $(pwd):/app --net rasa --name rasa --entrypoint="" rasa/rasa:3.0.4-spacy-en bash -c "rasa run --cors=\"*\""
```

Test the chat through RESTful API:
```
curl -H "Content-Type: application/json" -X POST -d "{\"message\": \"Hi\", \"sender\": \"1\"}" "0.0.0.0:5005/webhooks/rest/webhook"
```


## Basic front end

Copy the `index.html` file and put it in the project folder from this [github repo](https://github.com/RasaHQ/how-to-rasa/tree/main/video-10-connectors). Visit the [official github page](https://github.com/scalableminds/chatroom) of the project for more details. 

Launch the server typing the following commands (python version 3.8):
```
python -m http.server 8000
```

Make sure to run the Rasa chatbot with `--cors="*"` commands additionally one can use `--debug` command for debugging:
```
rasa run --cors="*" --port 5005
```

## Rasa project structure details

```
📂 /path/to/project
┣━━ 📂 actions                      # actions
┃   ┣━━ 📂 static                   # static files
┃   ┃   ┣━━ 🔢 plant_matches.pkl    # data scraped from "plant diagnostic matrix"
┃   ┃   ┗━━ 🔢 plant_tree.pkl       # data scraped from "plant diagnostic matrix"
┃   ┣━━ 🐍 __init__.py              #
┃   ┣━━ 🐍 actions.py               # actions main module
┃   ┣━━ 🐍 helper.py                # helper functions for actions module
┃   ┣━━ 🐍 plant_matching.ipynb     # EDA for scraped data
┃   ┗━━ 🐍 requirements-action.txt  # modules used in actions module
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
┣━━ 📄 index.html                   # HTML file for python web-client
┗━━ 📄 README.md                    # readme file
┗━━ 📄 endpoints.yml                # endpoints file
```

## Regarding Rasa X

Rasa X as of 04.01.2022 is not supported by Rasa 3.0.* - [source](https://rasa.com/docs/rasa-x/changelog/compatibility-matrix/). Support for [Rasa X for Rasa 3.0.*](https://forum.rasa.com/t/rasa-x-3-0/49700) is coming soon as authors say.

## `rasa-webchat` intergration

It is not compatible with `Rasa 3.0.*` since `rasa-webchat` requires `socket.io-client` be version of 3.1.2, but `Rasa 3.0.*` requires `python-socketio` (which `socketio` client) be later than 4.4 (and less than 6).

curl -H "Content-Type: application/json" -X POST http://0.0.0.0:5005/webhooks/rest/webhook -d "{\"message\": \"Flowers\", \"sender\": \"8428f3c3-23f2-4455-aedc-4c564c2616c7\"}"