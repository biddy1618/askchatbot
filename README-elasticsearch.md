# Elasticsearch for Askchatbot

# Installation

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



# Example Stackoverflow questions

References:

-  https://www.elastic.co/blog/text-similarity-search-with-vectors-in-elasticsearch
- https://github.com/jtibshirani/text-embeddings

```bash
git clone https://github.com/jtibshirani/text-embeddings.git
cd text-embeddings
conda create --name elasticsearch-stackoverflow python=3.7
conda activate elasticsearch-stackoverflow
pip install -r requirements.txt

# make sure the elasticsearch container is up & running
sudo docker ps -a
curl -XGET -u elastic:changeme 'localhost:9200/?pretty'

# populates the database & starts query loop
python src/main.py
> Downloading pre-trained embeddings from tensorflow hub...
> Injecting documents
> Enter query:

# also, check out the injected data with kibana

# to query with curl
#...todo... curl -X GET "localhost:9200/_xpack?pretty"
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