import os
import sys
import logging
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
username                = es_config.get('username'              , None)
password                = es_config.get('password'              , None)
tf_embed_url            = es_config.get('tfhub-embdedding-url'  , None)
tfhub_cache_dir         = es_config.get('tfhub-cache-dir'       , None)
tf_cpp_min_log_level    = es_config.get('tf-cpp-min-log-level'  , None)
es_askextension_index   = es_config.get('askextension-index'    , None)
es_combined_index       = es_config.get('combined-index'        , None)


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

# index mappings
ES_ASKEXTENSION_MAPPING     = json.load(open(f'{_PATH}/data/mappings/askextension_mapping.json'))
ES_COMBINED_VECTOR_MAPPING  = json.load(open(f'{_PATH}/data/mappings/combined_vector_mapping.json'))
ES_COMBINED_MAPPING         = json.load(open(f'{_PATH}/data/mappings/combined_mapping.json'))

logger.info('----------------------------------------------')
logger.info('Elasticsearch indexes:')
logger.info(f'- askextension index       = {es_askextension_index}')
logger.info(f'- combined index           = {es_combined_index    }')
logger.info('----------------------------------------------')


logger.info('Initializing the Elasticsearch client')
es_client = Elasticsearch([host], http_auth=(username, password))
logger.info('Done initiliazing ElasticSearch client')

logger.info(f'Start loading embedding module {tf_embed_url}')
embed = tf_hub.load(tf_embed_url)
logger.info(f'Done loading embedding module {tf_embed_url}')
# -------------------------------------------------------------

