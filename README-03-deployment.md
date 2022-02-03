# Deploy the chatbot w/ docker-compose

The bot is deployed at http://34.219.35.63:8000/

The architecture diagram can be found [here](https://docs.google.com/drawings/d/1h_DHiiTr2km3OKpcsoGScElEtyXSR3jL6PHumcRPwQI/edit).

### Install docker & docker-compose

For Ubuntu 20.04, you can just install Docker from a standard Ubuntu Repository

```bash
sudo apt-get update
sudo apt install docker.io docker-compose

sudo docker --version
19.03.#

sudo docker-compose --version
docker-compose version 1.25.0, build unknown
```

### Create conda environment

##### Install Miniconda3 for Ubuntu

```bash
# download Miniconda installer for Python 3.7
# (https://docs.conda.io/en/latest/miniconda.html)
$ wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Install Miniconda
$ chmod +x Miniconda3-latest-Linux-x86_64.sh
$ ./Miniconda3-latest-Linux-x86_64.sh
Do you accept the license terms? [yes|no]
[no] >>> yes
.
Do you wish the installer to initialize Miniconda3
by running conda init? [yes|no]
[no] >>> yes

# Verify it works
$ source ~/.bashrc  # installer updated this, and will activate the base environment
(base) > conda --version
```

```bash
git clone https://git.eduworks.us/ask-extension/askchatbot
cd askchatbot/askchatbot

conda create --name askchatbot python=3.7
conda activate askchatbot
pip install -r requirements-dev.txt
pip install -e .
```

### Create the elasticsearch index

See `README-01-elasticsearch.md`

### Build the docker image for the action server

For now, we build the docker image on the VM, and do not push it to a docker registry.

```bash
cd askchatbot

# get latest version of the github repo
git status
git stash push
git pull
git stash pop

#
# Edit the file: ./actions/bot_config.yml > select the correct elasticsearch host!

# Build the image
sudo docker-compose build

# To quickly test that the container starts up
sudo docker run -p 5055:5055 --add-host ask-chat-db-dev.i.eduworks.com:34.211.141.190 askchatbot-action-server:0.0.5

curl http://localhost:5055/actions

# use rasa shell to do a quick query, making sure it can reach the elasticsearch host
rasa shell
> hi
> I have a pest
> Ants
```



### Quick Installation using Docker Compose  ([docs](https://rasa.com/docs/rasa-x/deploy/))

Install Rasa X using these steps:

#### Download & run the install script

```bash
cd <project-root>/deploy/docker-compose/secret
curl -sSL -o install.sh https://storage.googleapis.com/rasa-x-releases/0.30.1/install.sh
sudo bash ./install.sh
```

#### Select Rasa & Rasa X versions

```bash
cd /etc/rasa

sudo vi .env
RASA_X_VERSION=0.31.4
RASA_VERSION=1.10.10
RASA_X_DEMO_VERSION=0.31.4

```

#### Define action server, with extra hosts for elasticsearch

```bash
cd /etc/rasa

sudo vi docker-compose.override.yml
version: '3.4'
services:
  app:
    image: askchatbot-action-server:0.0.5
  extra_hosts: 
    - "ask-chat-db-dev.i.eduworks.com:34.211.141.190"
```



#### Define Nginx port

```bash
cd /etc/rasa

sudo vi docker-compose.override.yml
services:
  nginx:
    ports:
      - "8000:8080"
```

#### Activate custom channels (Optional)

```bash
cd /etc/rasa

# to activate rest channel, add this to credentials.yml
rest:
```

#### Activate debug mode (Optional)

```bash
cd /etc/rasa

# to activate debug mode on rasa x & rasa containers, 
# rasa-x: add this to docker-compose.override.yml
version: '3.4'
  
services:
  rasa-x:
    environment:
      DEBUG_MODE: "true"

# rasa: Add '--debug' directly to docker-compose.yml
x-rasa-services: &default-rasa-service
  command: >
    x
    --no-prompt
    --production
    --config-endpoint http://rasa-x:5002/api/config?token=${RASA_X_TOKEN}
    --port 5005
    --jwt-method HS256
    --jwt-secret ${JWT_SECRET}
    --auth-token '${RASA_TOKEN}'
    --cors "*"
    --debug
```

#### Deploy

```bash
cd /etc/rasa

# start the docker containers. -d will run it in the background
sudo docker-compose up -d  

# to bring down the deployment
sudo docker-compose down
```

Note that upon startup, the action server container downloads the pre-trained embedding model from `tfhub`. This takes a few minutes, and you have to wait until that is done before you can talk to the bot.

#### Set password of admin

This is not needed when upgrading without removing, because it is stored in the persistent Rasa X db.

```bash
cd /etc/rasa
sudo python rasa_x_commands.py create --update admin me <PASSWORD>
```

#### Upload & activate a trained model

Log into Rasa X at http://34.219.35.63:8000

Go to the `models` screen, and click on `upload model`

Upload a trained model from your local computer.

#### Monitor containers & their logs

```bash
# see the running containers
sudo docker ps -a

# view all the logs at once
sudo docker-compose logs --follow --tail 10

# view all the logs at once & tee them to a file
sudo docker-compose logs --follow --tail 10 | sudo tee logs-01.txt

# view the logs of a certain container
sudo docker logs rasa_rasa-x_1
```



#### Some checks

```bash
# version of rasa x
http://34.219.35.63:8000/api/version  # rasa-x

# check action server endpoints directly on the VM
curl http://localhost:5055/health  
curl http://localhost:5055/actions 
```



#### Check versions of Rasa X, Rasa & Rasa SDK

```bash
# do this on the VM
$ sudo docker ps -a

# Rasa X & Rasa , by hitting endpoint
$ curl http://localhost:8000/api/version

# For rasa-sdk, you need to go into the container
$ sudo docker exec -it rasa_app_1 cat rasa_sdk/version.py

```



#### Check health via curl on EC2

```bash
curl http://localhost:8000/api/version
```



#### Connect to Rasa X from browser

Rasa X is available on: http://34.219.35.63:8000/

#### Connect Rasa X to gitlab ([docs](https://rasa.com/docs/rasa-x/installation-and-setup/integrated-version-control/))

See [Jira AE-314](https://jira.eduworks.us/browse/AE-314) for Rasa X to Gitlab connection.

### Share the bot with guest testers

To create a link that you can share with guest testers, follow [these instructions](https://rasa.com/docs/rasa-x/user-guide/share-assistant/#share-your-bot).

### Maintain disk space

The disk space will keep going up, and these are some typical maintenance steps to check & reduce.

```bash
# check available disk space
df -h /

# find large files on disk
sudo du -cha --max-depth=1 / | grep -E "M|G" | sort -h
```

#### Docker containers & images 

```bash
# clean up docker  (this is safe)
sudo docker system prune
```