# Miscallenous

## Alternative front-end set ups

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

## Regarding Rasa X

Rasa X as of 04.01.2022 is not supported by Rasa 3.0.* - [source](https://rasa.com/docs/rasa-x/changelog/compatibility-matrix/). Support for [Rasa X for Rasa 3.0.*](https://forum.rasa.com/t/rasa-x-3-0/49700) is coming soon as authors say.

## `rasa-webchat` intergration

It is not compatible with `Rasa 3.0.*` since `rasa-webchat` requires `socket.io-client` be version of 3.1.2, but `Rasa 3.0.*` requires `python-socketio` (which `socketio` client) be later than 4.4 (and less than 6).