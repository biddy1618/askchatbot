import os
import sys
import logging
from pathlib import Path
import json

from elasticsearch import AsyncElasticsearch

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

es_username     = os.getenv('ES_USERNAME'       , 'elastic'                 )
es_password     = os.getenv('ES_PASSWORD'       , 'changeme'                )
es_host         = os.getenv('ES_HOST'           , 'http://localhost:9200/'  )
tfhub_cache_dir = os.getenv('TFHUB_CACHE_DIR'   , '/var/tmp/tfhub_modules'  )

stage           = 'dev'
# stage           = 'prod'
version         = '04.06.22'
# tf_embed_url    = 'https://tfhub.dev/google/universal-sentence-encoder/4'
tf_embed_url    = 'https://tfhub.dev/google/universal-sentence-encoder-large/5'
es_imitate      = False

es_combined_index       = 'combined'
es_field_limit          = 32766
debug                   = stage == 'dev'

es_search_size          = 100
es_cut_off              = 0.4
es_top_n                = 10
es_ask_weight           = 0.6
es_slots_weight         = 0.3

if debug:

    logger.info('----------------------------------------------')
    logger.info('Configuration variables for DEV environment'   )
    logger.info(f'- stage           = {stage}'                  )
    logger.info(f'- es_search_size  = {es_search_size}'         )
    logger.info(f'- es_cut_off      = {es_cut_off}'             )
    logger.info(f'- es_top_n        = {es_top_n}'               )
    logger.info(f'- es_ask_weight   = {es_ask_weight}'          )
    logger.info(f'- es_slots_weight = {es_slots_weight}'        )
    logger.info('----------------------------------------------')


    _PATH = Path(__file__).parent.as_posix()

    # index mappings
    ES_COMBINED_MAPPING = json.load(open(f'{_PATH}/data/mappings/combined_mapping.json'))


if not es_imitate:

    import tensorflow_hub as tf_hub

    logger.info('----------------------------------------------')
    logger.info('Elasticsearch configuration:')
    logger.info(f'- host                = {es_host          }')
    if debug:
        logger.info(f'- username            = {es_username  }')
        logger.info(f'- password            = {es_password  }')
    logger.info(f'- tfhub_embedding_url = {tf_embed_url     }')
    logger.info(f'- tfhub_cache_dir     = {tfhub_cache_dir  }')
    logger.info('----------------------------------------------')


    logger.info('----------------------------------------------')
    logger.info('Elasticsearch indexes:')
    logger.info(f'- combined index      = {es_combined_index}')
    logger.info('----------------------------------------------')


    logger.info('Initializing the Elasticsearch client')
    es_client = AsyncElasticsearch([es_host], http_auth=(es_username, es_password))
    logger.info('Done initiliazing ElasticSearch client')

    logger.info(f'Start loading embedding module {tf_embed_url}')
    embed = tf_hub.load(tf_embed_url)
    logger.info(f'Done loading embedding module {tf_embed_url}')
    # -------------------------------------------------------------
else:
    logger.info('----------------------------------------------')
    logger.info('Imitating Elasticseach queries for dev purposes')
    logger.info('----------------------------------------------')

