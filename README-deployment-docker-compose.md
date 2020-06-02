# Deploy the chatbot w/ docker-compose

# Build & Push docker image of action server

This step is done on the local system in the cloned repo.

### Connect to the knowledge base instance

To connect to the knowledge base instance, configure the following in 
`<project-root>/credentials_knowledge_base.yml`:

- `kb_instance` - This is just the instance address, you don't need the leading https.
- `kb_user` - The username of the service account the action code will use to query the knowledge base.
- `kb_pw` - The password of the service account the action code will use to query the knowledge base.
- `localmode` -  When set to `true` (default in the code),  the action server will **not** send an actual query to the `kb_instance`. 

### Build docker image of action server

For now, we will build & push the docker image of the action server manually. You can run the commands locally or on the EC2 instance.

A Dockerfile is included in the project-root folder.

#### Build the docker image

```bash
to describe...
```

#### Test locally

```bash
to describe...
```

#### Push the docker image

```bash
to describe...
```



# Deploy

### Install Docker

For Ubuntu 20.04, you can just install Docker from a standard Ubuntu Repository

```bash
sudo apt install docker.io

sudo docker --version
19.03.#
```

### Quick Installation using Docker Compose  ([docs](https://rasa.com/docs/rasa-x/deploy/))

Use the [Quick Installation](https://rasa.com/docs/rasa-x/deploy/#quick-installation) method, with this detail:

#### Download & run the install script

```bash
cd <project-root>/deploy/docker-compose/secret
curl -sSL -o install.sh https://storage.googleapis.com/rasa-x-releases/0.28.5/install.sh
sudo bash ./install.sh
```

#### Select Rasa & Rasa X versions

```bash
cd /etc/rasa

sudo vi .env
RASA_X_VERSION=0.28.5
RASA_VERSION=1.10.1
RASA_X_DEMO_VERSION=0.28.5
```

#### Define action server

```bash
cd /etc/rasa

sudo vi docker-compose.override.yml
version: '3.4'
services:
  app:
    image: docker.io/arjaan/test:0.0.1
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

# rasa: Add this directly to docker-compose.yml
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
http://35.166.13.105:8000/api/version  # rasa-x

# check action server endpoints directly on the VM
curl http://localhost:5055/health  
curl http://localhost:5055/actions 
```



#### Set password of admin

```bash
cd /etc/rasa
sudo python rasa_x_commands.py create --update admin me <PASSWORD>
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

Rasa X is available on: http://35.166.13.105:8000/



#### Connect Rasa X to gitlab ([docs](https://rasa.com/docs/rasa-x/installation-and-setup/integrated-version-control/))

The bot is temporarily stored in personal, private repo on github.

From Rasa X, connect to the git repository as described in the docs.
