import os
import sys
import logging
from contextlib import suppress

from pathlib import Path
from ruamel import yaml
import json

from elasticsearch import Elasticsearch

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

_PATH = Path(__file__).parents[1].as_posix()

# -------------------------------------------------------------
# Define paths where data stored  
PATH_DATA_ASKEXTENSION  = f'{_PATH}/data/askextension/2020-08-20/'
PATH_DATA_UCIPM         = f'{_PATH}/data/uc-ipm/updated/'
PATH_DATA_RESULTS       = f'{_PATH}/data/transformed/'

if not os.path.exists(PATH_DATA_RESULTS):
    os.makedirs(PATH_DATA_RESULTS)

# Askexntension data
ASKEXTENSION_FILE_NAMES     = [f'{PATH_DATA_ASKEXTENSION}{f}' for f in os.listdir(PATH_DATA_ASKEXTENSION)]
ASKEXTENSION_FILE_RESULT    = PATH_DATA_RESULTS + 'askextension_transformed.json'
ASKEXTENSION_QUESTION_URL   = 'https://ask2.extension.org/kb/faq.php?id='

# UC IPM data
UCIPM_FILE_NAMES        = [f'{PATH_DATA_UCIPM}{f}' for f in os.listdir(PATH_DATA_UCIPM)]
# -------------------------------------------------------------



# -------------------------------------------------------------
# ES configuration
es_config = (yaml.safe_load(open(f'{_PATH}/src/es_config.yml', 'r')) or {})

host                    = es_config.get('host'                  , None)
tf_embed_url            = es_config.get('tfhub-embdedding-url'  , None)
tfhub_cache_dir         = es_config.get('tfhub-cache-dir'       , None)
tf_cpp_min_log_level    = es_config.get('tf-cpp-min-log-level'  , None)

# os.environ['TF_CPP_MIN_LOG_LEVEL']  = tf_cpp_min_log_level
os.environ['TFHUB_CACHE_DIR']       = tfhub_cache_dir

import tensorflow_hub as tf_hub

logger.info("----------------------------------------------")
logger.info("Elasticsearch configuration:")
logger.info("- host                     = %s", host)
# logger.info("- username                 = %s", pprint.pformat(username))
# logger.info("- password                 = %s", pprint.pformat(password))
# logger.info("- do_the_queries           = %s", do_the_queries)
# logger.info("- ipmdata_index_name       = %s", ipmdata_index_name)
logger.info("- tfhub_embedding_url      = %s", tf_embed_url)
logger.info("- tfhub_cache_dir          = %s", tfhub_cache_dir)
logger.info("----------------------------------------------")

# index mappings
ES_ASKEXTENSION_MAPPING     = json.load(open(f'{_PATH}/data/mappings/askextension_mapping.json'))
ES_COMBINED_MAPPING_VECTOR  = json.load(open(f'{_PATH}/data/mappings/combined_mapping_vector.json'))
ES_COMBINED_MAPPING         = json.load(open(f'{_PATH}/data/mappings/combined_mapping.json'))

ES_ASKEXTENSION_INDEX   = es_config.get('askextension-index', None)
ES_COMBINED_INDEX       = es_config.get('combined-index'    , None)

logger.info("----------------------------------------------")
logger.info("Elasticsearch indexes:")
logger.info("- askextension index       = %s", ES_ASKEXTENSION_INDEX)
logger.info("- combined index           = %s", ES_COMBINED_INDEX)
# logger.info("- username                 = %s", pprint.pformat(username))
# logger.info("- password                 = %s", pprint.pformat(password))
# logger.info("- do_the_queries           = %s", do_the_queries)
# logger.info("- ipmdata_index_name       = %s", ipmdata_index_name)
# logger.info("- mapping                  = \n%s", json.dumps(askextension_mapping, indent=4))
logger.info("----------------------------------------------")


logger.info("Initializing the Elasticsearch client")
es_client = Elasticsearch(host)
logger.info("Done initiliazing ElasticSearch client")

logger.info("Start loading embedding module %s", tf_embed_url)
embed = tf_hub.load(tf_embed_url)
logger.info("Done loading embedding module %s", tf_embed_url)
# -------------------------------------------------------------

