"""Configuration of action server"""

import os
import logging
import pprint
from pathlib import Path
import ruamel.yaml
import tensorflow_hub as tf_hub
from elasticsearch import Elasticsearch
from ssl import create_default_context

logger = logging.getLogger(__name__)

##########
# Rasa X #
##########
# - default: action server deployed on same docker network
rasa_x_host = os.environ.get("RASA_X_HOST", "rasa-x:5002")

logger.info("----------------------------------------------")
logger.info("Rasa X configuration:")
logger.info("- rasa_x_host = %s", rasa_x_host)
logger.info("----------------------------------------------")

#################
# Elasticsearch #
#################
es_config = (
    ruamel.yaml.safe_load(
        open(f"{Path(__file__).parents[0]}/credentials_elasticsearch.yml", "r")
    )
    or {}
)

hosts = es_config.get("hosts", None)
username = es_config.get("username", None)
password = es_config.get("password", None)
do_the_queries = es_config.get("do-the-queries")
ipmdata_index_name = es_config.get("ipmdata-index-name")
tfhub_embedding_url = es_config.get("tfhub-embedding-url")
search_size = es_config.get("search-size")

# initialize the elastic search client
logger.info("Initializing the elasticsearch client")
context = create_default_context(cafile=f"{Path(__file__).parents[0]}/cert.pem")
es_client = Elasticsearch(
        hosts, 
        http_auth=(username, password),
        ssl_context=context
        )


logger.info("----------------------------------------------")
logger.info("Elasticsearch configuration:")
logger.info("- hosts                    = %s", pprint.pformat(hosts))
logger.info("- username                 = %s", pprint.pformat(username))
logger.info("- password                 = %s", pprint.pformat(password))
logger.info("- do_the_queries           = %s", do_the_queries)
logger.info("- ipmdata_index_name     = %s", ipmdata_index_name)
logger.info("- tfhub_embedding_url      = %s", tfhub_embedding_url)
logger.info("----------------------------------------------")

####################
# TFHUB embeddings #
####################
# define where the tfhub modules are stored
os.environ["TFHUB_CACHE_DIR"] = es_config.get("tfhub-cache-dir")

logger.info("Start loading embedding module %s", tfhub_embedding_url)
embed = tf_hub.load(tfhub_embedding_url)
logger.info("Done loading embedding module %s", tfhub_embedding_url)
