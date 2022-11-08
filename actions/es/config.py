import os
import sys
import logging
import pickle

from spacy.lang.en import English

from elasticsearch import AsyncElasticsearch

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

es_username     = os.getenv('ES_USERNAME'       , 'elastic'                 )
es_password     = os.getenv('ES_PASSWORD'       , 'changeme'                )
es_host         = os.getenv('ES_HOST'           , 'https://dev.ucipm.es.chat.ask.eduworks.com/'  )
embed_cache_dir = os.getenv('TFHUB_CACHE_DIR'   , '/var/tmp/models'         )

es_imitate  = False
version     = '29.06.22'
stage       = 'dev'
# stage       = 'prod'
expert_url  = 'https://ucanr.edu/About/Locations/'
client = "uc_ipm"
embed_url = "JeffEduworks/generalized_chatbot_model"
auth_token = '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'
es_combined_index   = 'combined'
es_logging_index    = 'logs'
es_field_limit      = 32766
debug               = stage == 'dev'

es_search_size  = 100
es_cut_off      = 0.4
es_top_n        = 10
es_ask_weight   = 0.8
es_downweight   = 1

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

logger.info('----------------------------------------------')
logger.info('Loading hardcoded queries')
hardcoded_queries       = []
es_cut_off_hardcoded    = es_cut_off + 0.2
es_hardcoded_threshold  = 0.85
try:
    with open(os.path.join(os.path.dirname(__file__), 'scripts/hardcoded/transformed/hardcoded.pickle'), 'rb') as handle:
        hardcoded_queries = pickle.load(handle)
    logger.info('Successfully loaded hardcoded queries')
except IOError:
    logger.info('Failed loading hardcoded queries')
logger.info(f'- cut off parameter for hardcoded queries     = {es_cut_off_hardcoded:.2f}'   )
logger.info(f'- cut off parameter for similarity threshold  = {es_hardcoded_threshold:.2f}' )
logger.info('----------------------------------------------')

if debug:

    logger.info('----------------------------------------------')
    logger.info('Configuration variables for DEV environment')
    logger.info(f'- stage           = {stage}')
    logger.info(f'- expert_url      = {expert_url}')
    logger.info(f'- es_search_size  = {es_search_size}')
    logger.info(f'- es_cut_off      = {es_cut_off}')
    logger.info(f'- es_top_n        = {es_top_n}')
    logger.info(f'- es_ask_weight   = {es_ask_weight}')
    logger.info('----------------------------------------------')

if not es_imitate:

    # import tensorflow_hub as tf_hub
    from sentence_transformers import SentenceTransformer

    logger.info('----------------------------------------------')
    logger.info('Elasticsearch configuration:')
    logger.info(f'- host                = {es_host          }')
    if debug:
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

    logger.info('Initializing the Elasticsearch client')
    es_client = AsyncElasticsearch(
        [es_host], http_auth=(es_username, es_password))
    logger.info('Done initiliazing ElasticSearch client')

    logger.info(f'Start loading embedding module - {embed_url}')
    
    
    embed = SentenceTransformer(
        model_name_or_path  = embed_url         ,
        use_auth_token      = auth_token        ,
        cache_folder        = embed_cache_dir   ,
        device              = 'cpu'             )
    logger.info(f'Done loading embedding module - {embed_url}')
    # -------------------------------------------------------------
else:
    logger.info('----------------------------------------------')
    logger.info('Imitating Elasticseach queries for dev purposes')
    logger.info('----------------------------------------------')
