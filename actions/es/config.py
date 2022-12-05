'''
Module for configuration.

Author: Dauren Baitursyn
'''
import os
import sys
import logging
import pickle

from spacy.lang.en import English
from elasticsearch import AsyncElasticsearch
from sentence_transformers import SentenceTransformer
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


# ES configuration variables
es_username     = os.getenv('ES_USERNAME'       , 'elastic'                 )
es_password     = os.getenv('ES_PASSWORD'       , 'changeme'                )
es_host = os.getenv("ES_HOST", '127.0.0.1:9200')
es_client = AsyncElasticsearch([es_host], http_auth=(es_username, es_password))


#stage = 'dev' if 'dev' in es_host else 'prod'
stage = 'dev'

# Cache directory for sentence embedder
embed_cache_dir = os.getenv('TFHUB_CACHE_DIR'   , '/var/tmp/models'         )
embed_url = "JeffEduworks/generalized_chatbot_model"
expert_url  = 'https://ucanr.edu/About/Locations/'
auth_token = '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'

# Front-end configs
## Static
es_combined_index   = 'combined'
es_logging_index    = 'logs'
es_field_limit      = 32766

## Dynamic
search_size         = 100
max_return_amount   = 10
cut_off             = 0.6
ae_downweight       = 0.85

config_keys = {"search_size", "cut_off", "max_return_amount", "ae_downweight"}

# Loading synonym procedure
logger.info('----------------------------------------------')
logger.info('Loading synonym procedure')
tokenizer = English().tokenizer
synonym_dict = {}
try:
    with open(os.path.join(os.path.dirname(__file__), 'scripts/synonym_list/transformed/synonym_pest.pickle'), 'rb') as handle:
        synonym_dict = pickle.load(handle)
    logger.info('Successfully loaded synonym list')
except IOError:
    logger.info('Failed loading synonym list')
logger.info('----------------------------------------------')

# Loading hardcoded queries
logger.info('----------------------------------------------')
logger.info('Loading hardcoded queries')
hardcoded_queries       = []
es_hardcoded_threshold  = 0.85
try:
    with open(os.path.join(os.path.dirname(__file__), 'scripts/hardcoded/transformed/hardcoded.pickle'), 'rb') as handle:
        hardcoded_queries = pickle.load(handle)
    logger.info('Successfully loaded hardcoded queries')
except IOError:
    logger.info('Failed loading hardcoded queries')
logger.info(f'- cut off parameter for hardcoded queries     = {cut_off:.2f}'   )
logger.info('----------------------------------------------')

# Debug messages
if stage == 'dev':
    logger.info('----------------------------------------------')
    logger.info('Configuration variables for DEV environment')
    logger.info(f'- stage               = {stage}')
    logger.info(f'- expert_url          = {expert_url}')
    logger.info(f'- search_size         = {search_size}')
    logger.info(f'- cut_off             = {cut_off}')
    logger.info(f'- max_return_amount   = {max_return_amount}')
    logger.info(f'- ae_downweight       = {ae_downweight}')
    logger.info('----------------------------------------------')

logger.info('----------------------------------------------')
logger.info('Elasticsearch configuration:')
logger.info(f"ES Host: {es_host}")
if stage == 'dev':
    logger.info(f'- username            = {es_username  }')
    logger.info(f'- password            = {es_password  }')
logger.info(f'- embed_url           = {embed_url        }')
logger.info(f'- embed_cache_dir     = {embed_cache_dir  }')
logger.info('----------------------------------------------')
logger.info('----------------------------------------------')

logger.info('Elasticsearch indexes:')
logger.info(f'- combined index      = {es_combined_index}'  )
logger.info(f'- logging index       = {es_logging_index}'   )
logger.info('----------------------------------------------')

logger.info(f'Start loading embedding module - {embed_url}')
embed = SentenceTransformer(
    model_name_or_path  = embed_url         ,
    use_auth_token      = auth_token        ,
    cache_folder        = embed_cache_dir   ,
    device              = 'cpu'             )
logger.info(f'Done loading embedding module - {embed_url}')
