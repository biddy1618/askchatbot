"""Configuration of action server"""

import os
import logging
import pprint
from pathlib import Path
from ssl import create_default_context
import ruamel.yaml
import tensorflow_hub as tf_hub
from elasticsearch import Elasticsearch


logger = logging.getLogger(__name__)

botconfig = (
    ruamel.yaml.safe_load(open(f"{Path(__file__).parents[0]}/bot_config.yml", "r"))
    or {}
)

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
hosts = botconfig.get("hosts", None)
username = botconfig.get("username", None)
password = botconfig.get("password", None)
do_the_queries = botconfig.get("do-the-queries")
ipmdata_index_name = botconfig.get("ipmdata-index-name")
tfhub_embedding_url = botconfig.get("tfhub-embedding-url")
search_size = botconfig.get("search-size")

# initialize the elastic search client
logger.info("Initializing the elasticsearch client")
context = create_default_context(cafile=f"{Path(__file__).parents[0]}/cert.pem")
es_client = Elasticsearch(hosts, http_auth=(username, password), ssl_context=context)


logger.info("----------------------------------------------")
logger.info("Elasticsearch configuration:")
logger.info("- hosts                    = %s", pprint.pformat(hosts))
logger.info("- username                 = %s", pprint.pformat(username))
# logger.info("- password                 = %s", pprint.pformat(password))
logger.info("- do_the_queries           = %s", do_the_queries)
logger.info("- ipmdata_index_name       = %s", ipmdata_index_name)
logger.info("- tfhub_embedding_url      = %s", tfhub_embedding_url)
logger.info("----------------------------------------------")

####################
# TFHUB embeddings #
####################
# define where the tfhub modules are stored
os.environ["TFHUB_CACHE_DIR"] = botconfig.get("tfhub-cache-dir")

logger.info("Start loading embedding module %s", tfhub_embedding_url)
embed = tf_hub.load(tfhub_embedding_url)
logger.info("Done loading embedding module %s", tfhub_embedding_url)

##############################
# Default bot configurations #
##############################
bot_config_debug = botconfig.get("bot-config-debug")
# bot_config_weight_description = botconfig.get("bot-config-weight-description")
# bot_config_weight_damage = botconfig.get("bot-config-weight-damage")
bot_config_score_threshold = botconfig.get("bot-config-score-threshold")
bot_config_botname = botconfig.get("bot-config-botname")
bot_config_urlprivacy = botconfig.get("bot-config-urlprivacy")

logger.info("----------------------------------------------")
logger.info("Bot configuration:")
logger.info("- bot_config_debug              = %s", bot_config_debug)
# logger.info("- bot_config_weight_description = %s", bot_config_weight_description)
# logger.info("- bot_config_weight_damage      = %s", bot_config_weight_damage)
logger.info("- bot_config_score_threshold    = %s", bot_config_score_threshold)
logger.info("- bot_config_botname            = %s", bot_config_botname)
logger.info("- bot_config_urlprivacy         = %s", bot_config_urlprivacy)
logger.info("----------------------------------------------")
