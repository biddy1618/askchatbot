# Local set up

Install required libraries for packages to run without issues (try without these first):
```
sudo apt install pkg-config libxml2-dev libxmlsec1-dev libxmlsec1-openssl
```

Install miniconda version:
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod +x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh
```

Create environment for the chatbot:
```
conda --version
conda create --name askchatbot python=3.7
conda activate askchatbot
```

First set up:
```
pip install --upgrade pip
pip cache purge
pip install rasa
pip install --upgrade sanic==21.6.1
pip install ipykernel
pip install pandas
```

__BUT__ to avoid conflicts, please use `requirements.txt` file:
```
pip cache purge
pip install -r ./rasa-dev/requirements.txt
```

## Basic front end

Copy the `index.html` file and put it in the project folder from this [github repo](https://github.com/RasaHQ/how-to-rasa/tree/main/video-10-connectors). Visit the [official github page](https://github.com/scalableminds/chatroom) of the project for more details. 

Launch the server typing the following commands:
```
python -m http.server 8000
```

Make sure to run the Rasa chatbot with `--enable-api` and `--cors="*"` commands, additionally one can use `--debug` command for debugging:
```
rasa run --enable-api --cors="*" --debug --port 5005
```

## Installing Rasa X

Follow the guidelines for Rasa 1.0.x on [site](https://rasa.com/docs/rasa-x/installation-and-setup/install/rasa-ephemeral-installer/installation#quickstart).

```
curl -O https://rei.rasa.com/rei.sh && bash rei.sh -y
rasactl start --project
```

To check the status and find out the url, run the following:
```
rasactl status
```

__IMPORTANT NOTE__: Rasa X as of 04.01.2022 is not supported by Rasa 3.0.* - [source](https://rasa.com/docs/rasa-x/changelog/compatibility-matrix/). Support for [Rasa X for Rasa 3.0.*](https://forum.rasa.com/t/rasa-x-3-0/49700) is coming soon, so stay tuned for updates.

## `rasa-webchat` intergration

It is not compatible with `Rasa 3.0.*` since `rasa-webchat` requires `socket.io-client` be version of 3.1.2, but `Rasa 3.0.*` requires `python-socketio` (which `socketio` client) be later than 4.4 (and less than 6).