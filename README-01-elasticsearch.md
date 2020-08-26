# Elasticsearch for Askchatbot

The bot does elastic search queries, and this README explains how to create the index.

# Elasticsearch instance

For local development, it is useful to install elastic search locally with docker-compose, as described in Appendix A.

For deployment, elasticsearch was deployed on a dedicated EC2 instance. Details, including password, can be found in this [Jira Ticket](https://jira.eduworks.us/browse/AE-283?focusedCommentId=31925&page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel#comment-31925)

For the Elasticsearch EC2 instance, on the connecting machine add to /etc/hosts:

```bash
34.211.141.190 ask-chat-db-dev.i.eduworks.com
```

- User: elastic
- PW:  see [Jira Ticket](https://jira.eduworks.us/browse/AE-283?focusedCommentId=31925&page=com.atlassian.jira.plugin.system.issuetabpanels:comment-tabpanel#comment-31925)

You can test it from the command line with:

```bash
# Check it is up & running
curl -u elastic:<password> 'https://ask-chat-db-dev.i.eduworks.com:9200/?pretty'

# Submit a _cat/nodes request to see that the nodes are up and running
curl -u elastic:<password> 'https://ask-chat-db-dev.i.eduworks.com:9200/_cat/nodes?v&"

# Get an overview of all indices
curl -u elastic:<password> 'https://ask-chat-db-dev.i.eduworks.com:9200/_cat/indices?v'
```



# Create & Test the index

### Conda

```bash
conda create --name askchatbot python=3.7
conda activate askchatbot

git clone https://git.eduworks.us/ask-extension/askchatbot
cd askchatbot/askchatbot
pip install -r requirements-dev.txt
pip install -e .
```

### ETL

The scraped JSON files from the [ipm website](http://ipm.ucanr.edu/) can be placed as is in the `ipmdata` folder, which is included in the gitlab repo:

```bash
askchatbot/askchatbot/scripts/elasticsearch/data/ipmdata:
- cleanedPestDiseaseItems.json
- cleanedTurfPests.json
- cleanedWeedItems.json
- cleanedExoticPests.json
- ipmdata.json
```

The JSON scraped from the [askextension ostickets](https://osticket.eduworks.com/kb/faq.php?id=675271) requires some processing. Download [the scraped JSON files](https://drive.google.com/drive/folders/14iXEta0_dFsjAtBKM510mM78H3iVku8o?usp=sharing) in a folder on your computer and then run the ETL script `etl_askextension.py`:

```bash
cd askchatbot/askchatbot/scripts/elasticsearch/src
python -m etl_askextension
```

The ETL script will create a file in the `ipmdata` folder:

```bash
askchatbot/askchatbot/scripts/elasticsearch/data/ipmdata:
- askextensiondata-california.json
```

### Ingest

The script to ingest the documents into elasticsearch uses code & configuration settings from the bots' custom action code.

```bash
# When deploying on the EC2 instance, first get latest version of the github repo
cd askchatbot
git status
git stash push
git pull
git stash pop

# Before starting the ingesting process, stop the bot, else the EC2 will run out of memory
cd /etc/rasa
sudo docker-compose down

# Edit the file: askchatbot/askchatbot/actions/bot_config.yml
# (1) Uncomment the correct host, for example a local version as described in Appendix A,
#  or this version that is used by the deployed bot:
hosts: "https://ask-chat-db-dev.i.eduworks.com:9200/"
#
# (2) Uncomment the sentence encoder you want to use
# tfhub-embedding-url: "https://tfhub.dev/google/universal-sentence-encoder/4"
tfhub-embedding-url: "https://tfhub.dev/google/universal-sentence-encoder-large/5"
    
# Uncomment the correct index name of ipmdata queries
#ipmdata-index-name: "ipmdata-dev-large-5"
ipmdata-index-name: "ipm-and-ask-large-5"

# ingest the ipmdata
cd askchatbot/askchatbot/scripts/elasticsearch/src
python3 -m create_es_index

# You can now restart the bot
cd /etc/rasa
sudo docker-compose up -d
```

### Test

```bash
# to verify the index is there
curl -u elastic:<password> 'https://ask-chat-db-dev.i.eduworks.com:9200/_aliases?pretty'

# run a test query
python3 -m run_es_query
```



 

# Appendix A: Local docker-compose 

Installing Elasticsearch locally with docker-compose is useful for testing & development.

### Elasticsearch+kibana with docker-compose ([docs](https://www.elastic.co/guide/en/elastic-stack-get-started/current/get-started-docker.html))

(Very good reference also here: See https://github.com/deviantony/docker-elk)

#### increase virtual Memory ([docs](https://www.elastic.co/guide/en/elasticsearch/reference/current/vm-max-map-count.html))

Elasticsearch uses a [`mmapfs`](https://www.elastic.co/guide/en/elasticsearch/reference/current/index-modules-store.html#mmapfs) directory by default to store its indices. The default operating system limits on mmap counts is likely to be too low, which may result in out of memory exceptions during startup, like this:

```bash
[1]: max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]
```

On Ubuntu:

```bash
# check value
sysctl vm.max_map_count
> vm.max_map_count = 65530

# to increase value permanently, add to bottom of /etc/sysctl.conf
vm.max_map_count=262144

# then reload configuration
sudo sysctl -p
```

#### create a folder from where to deploy

```bash
mkdir -p ~/deploy/elastic/docker-compose
cd ~/deploy/elastic/docker-compose
```

#### `docker-compose.yml` for a one node cluster 

(see  ([docs](https://www.elastic.co/guide/en/elastic-stack-get-started/current/get-started-docker.html)) for multi-node)

```bash
version: '2.2'
services:
  es01:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.7.0
    container_name: es01
    environment:
      - node.name=es01
      - discovery.type=single-node
      - bootstrap.memory_lock=true
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ulimits:
      memlock:
        soft: -1
        hard: -1
    volumes:
      - data01:/usr/share/elasticsearch/data
    ports:
      - 9200:9200
    networks:
      - elastic

  kib01:
    image: docker.elastic.co/kibana/kibana:7.7.0
    container_name: kib01
    ports:
      - 5601:5601
    environment:
      ELASTICSEARCH_URL: http://es01:9200
      ELASTICSEARCH_HOSTS: http://es01:9200
    networks:
      - elastic

volumes:
  data01:
    driver: local

networks:
  elastic:
    driver: bridge
```

#### Deploy

```bash
cd ~/deploy/elastic/docker-compose

# deploy
sudo docker-compose up -d

# to bring down, with associated volume
sudo docker-compose down -v
```

#### Test ElasticSearch

```bash
# Elasticsearch is now running on port 9200. Verify it is working.
# For installation without authentication enabled
curl -XGET 'localhost:9200/?pretty'  

# For installation with authentication enabled via X-Pack
# -> default username & password = elastic:changeme
curl -XGET -u elastic:changeme 'localhost:9200/?pretty'    

# Submit a _cat/nodes request to see that the nodes are up and running
curl -X GET "localhost:9200/_cat/nodes?v&pretty"
ip          heap.percent ram.percent cpu load_1m load_5m load_15m node.role master name
172.20.0.3  25           69          20   0.93   0.97    0.99     dilmrt    *      es01
```

#### Test Kibana

Open browser at http://localhost:5601

# Appendix B: Stackoverflow posts

This is a good example to play around with, to become familiar with the elasticsearch approach to embedding vectors. 

References:

-  https://www.elastic.co/blog/text-similarity-search-with-vectors-in-elasticsearch
- https://github.com/jtibshirani/text-embeddings

```bash
# first time:
git clone https://git.eduworks.us/ask-extension/text-embeddings

# after that:
git fetch --all


cd text-embeddings
conda create --name es-so python=3.7
conda activate es-so
pip install -r requirements.txt

# make sure the elasticsearch container is up & running
sudo docker ps -a
curl -XGET -u elastic:changeme 'localhost:9200/?pretty'

# Create the elasticsearch index for the Stackoverflow posts
python3 src/create_es_index.py

# Run elasticsearch queries from the command line
python3 src/run_es_query.py
```

#### How does it work

##### First, Elasticsearch is populated from these files in the [text-embeddings repository](https://git.eduworks.us/ask-extension/text-embeddings):

- <text-embeddings-repo>/data/posts/posts.json

  A file where each line is a post in json format:

  ```json
  # type=question
  {"user":"8",
   "creationDate":"2008-07-31T21:42:52.667",
   "title":"While applying opacity...",
   "questionId":"4",
   "acceptedAnswerId":"7",
   "tags":["c#","winforms","type-conversion","decimal","opacity"],
   "body":"I want to use a track-bar...",
   "type":"question"}
  
  # type=answer
  {"user":"9",
   "creationDate":"2008-07-31T22:17:57.883",
   "questionId":"4",
   "answerId":"7",
   "body":"An explicit cast....",
   "type":"answer",}
  ```

  

- <text-embeddings-repo>/data/posts/index.json

  ```json
  {"settings": {"number_of_shards": 2, "number_of_replicas": 1},
   "mappings": {
       "dynamic": "true", 
       "_source": {"enabled": "true"},
       "properties": {
            "user": { "type": "keyword"},
            "creationDate": { "type": "date"},
            "title": {"type": "text"},
            "title_vector": {"type": "dense_vector","dims": 512},
            "questionId": {"type": "keyword"},
            "answerId": {"type": "keyword"},
            "acceptedAnswerId": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "body": {"type": "text"},
            "type": {"type": "keyword"}
      }
    }
  }
  ```

  Note the `title_vector`, which is of type `dense_vector`.

  That is a vector created for the title of each Stackoverflow question, using a tfhub embedding module

##### Then, we query elastic search from a custom action:

- User provides a stackoverflow question
- We create an vector using the exact same tfhub embedding module
- We query elasticsearch, with a cosine similarity against the `title_vector`
- We limit response to the top 5 scores, and show those to the user. 