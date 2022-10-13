# Local set up

Instructions for linux-based machines.

Details of the local machine:
- Memory: 23.3 GiB
- Processor: 11th Gen Intel® Core™ i7-11370H @ 3.30GHz × 8
- Graphics: NVIDIA Corporation / NVIDIA GeForce RTX 3060 Laptop GPU/PCIe/SSE2
- Disk Capacity: 1.0 TB
- OS Name: Ubuntu 20.04.4 LTS
- OS Type: 64-bit
- GNOME version: 3.36.8
- Windowing System: X11


## 1st method - `conda` environment (version 4.13.0)

Create environment with python version 3.9.12
```bash
conda create --yes --name askchatbot-dev python=3.9.12
conda activate askchatbot-dev
pip install pip==21.3.1
```

Install requirements for Rasa service:
```bash
pip install -r requirements.txt
pip install -r requirements-update.txt
pip install -r requirements-local.txt
```

Install requirements for Rasa Actions service:
```bash
pip install -r actions/requirements.txt
pip install -r actions/requirements-update.txt
```

Download spacy model:
```bash
python -m spacy download en_core_web_trf
```

Make sure that environment variables set correctly by running following command:
```bash
source env-dev.sh
```

Start Rasa service:
```bash
rasa run --cors=*
```

Start Rasa Actions service:
```bash
rasa run actions
```

## 2nd method (preferred) - `docker dompose` (version 2.2.2)

Launch the services up using `docker compose`:
```bash
docker compose build    # if you already built images, omit
docker compose up
```

FYI, the environment variables are set up in `.env` file:
```bash
# Elasticsearch settings
ES_USERNAME=elastic
ES_PASSWORD=changeme
## Change Elasticsearch host accordingly
## This one works if ES is available in host's localhost
# ES_HOST=http://host.docker.internal:9200/
## Otherwise this one for ES service on dev
ES_HOST=https://dev.es.chat.ask.eduworks.com/
## or this one for qa environment
# ES_HOST=https://qa.es.chat.ask.eduworks.com/
```

If you have already built the images, run the following to resume:
```bash
docker compose start
```

And to remove stopped containers and they are no longer needed, run following:
```bash
docker compose down
```

__NOTE__: 
> The endpoint for Elasticsearch service is set up by default at `https://dev.es.chat.ask.eduworks.com/` (as indicated at `.env` file).  
If you would like to run your own instance of ES locally, please, refer to file at [`README-1-es-deployment`](/actions/es/deployment/README-1-es-deployment.md) in this project.  
Follow the instuction in [`README-2-es-ingesting-data`](/actions/es/deployment/README-2-es-ingesting-data.md) for ingesting data into ES service, and you should be ready to go.

## Testing

Test the Rasa Chatbot through RESTful API (should return response for message "Hi"):
```bash
curl -H "Content-Type: application/json" -X POST -d "{\"message\": \"Hi\", \"sender\": \"1\"}" "localhost:5005/webhooks/rest/webhook"
```

To test the connection to ES, run the following in the python shell of __rasa-actions__ container:
```python
import requests
from requests.auth import HTTPBasicAuth 

# if ES is set up locally
# requests.get('http://host.docker.internal:9200/', auth=HTTPBasicAuth('elastic', 'changeme')).json()
# if ES is set up remotely (i.e. https://dev.es.chat.ask.eduworks.com)
requests.get('https://dev.es.chat.ask.eduworks.com/', auth=HTTPBasicAuth('elastic', 'changeme')).json()
```
It should return something like:
```bash
{'name': 'es01', 'cluster_name': 'docker-cluster', 'cluster_uuid': 'dwAXMxkPS7mOjAk7F9vE5A', 'version': {'number': '7.17.0', 'build_flavor': 'default', 'build_type': 'docker', 'build_hash': 'bee86328705acaa9a6daede7140defd4d9ec56bd', 'build_date': '2022-01-28T08:36:04.875279988Z', 'build_snapshot': False, 'lucene_version': '8.11.1', 'minimum_wire_compatibility_version': '6.8.0', 'minimum_index_compatibility_version': '6.0.0-beta1'}, 'tagline': 'You Know, for Search'}
```

## Front end

### Setting up [front-end project](https://git.eduworks.us/ask-extension/askchatbot-widget) locally 

Clone the project (`dev` branch), create file `.env` and set the variable `VUE_APP_API_URL` to `http://127.0.0.1:5005/webhooks/rest/webhook` in `.env` file:
```bash
VUE_APP_API_URL=http://127.0.0.1:5005/webhooks/rest/webhook
```

and run the docker while exposing 8081 port:
```bash
docker build -t front-end .
docker run -d -p 8081:8081 --name web-client front-end
```

You should be able to access the front-end at `http://localhost:8081/`.

__NOTE__:
> To test if CORS is enabled or not in our RESTful API (enabled by default) try following commands in the terminal:
```bash
SOURCE_URL=http://some-random-site
TARGET_URL=http://localhost:5005
curl -X OPTIONS -H "Origin: ${SOURCE_URL}" --head ${TARGET_URL}
```  
> It should output following:
```bash
Access-Control-Allow-Origin: ${SOURCE_URL} # http://some-random-site
```