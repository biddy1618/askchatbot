import os
import sys
import logging
from pathlib import Path
from ruamel import yaml

from elasticsearch import Elasticsearch

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

_PATH = Path(__file__).parent.as_posix()

# -------------------------------------------------------------
# ES configuration
es_config = (yaml.safe_load(open(f'{_PATH}/config.yml', 'r')) or {})

host                    = es_config.get('host'                  , None)
username                = es_config.get('username'              , None)
password                = es_config.get('password'              , None)
tf_embed_url            = es_config.get('tfhub-embdedding-url'  , None)
tfhub_cache_dir         = es_config.get('tfhub-cache-dir'       , None)
tf_cpp_min_log_level    = es_config.get('tf-cpp-min-log-level'  , None)
es_combined_index       = es_config.get('combined-index'        , None)

imitate = False

os.environ['TF_CPP_MIN_LOG_LEVEL']  = tf_cpp_min_log_level
os.environ['TFHUB_CACHE_DIR']       = tfhub_cache_dir

import tensorflow_hub as tf_hub

logger.info('----------------------------------------------')
logger.info('Elasticsearch configuration:')
logger.info(f'- host                     = {host            }')
logger.info(f'- username                 = {username        }')
logger.info(f'- password                 = {password        }')
logger.info(f'- tfhub_embedding_url      = {tf_embed_url    }')
logger.info(f'- tfhub_cache_dir          = {tfhub_cache_dir }')
logger.info('----------------------------------------------')

logger.info("Initializing the Elasticsearch client")
es_client = Elasticsearch([host], http_auth=(username, password))
logger.info("Done initiliazing ElasticSearch client")

logger.info("Start loading embedding module %s", tf_embed_url)
embed = tf_hub.load(tf_embed_url)
logger.info("Done loading embedding module %s", tf_embed_url)
# -------------------------------------------------------------

