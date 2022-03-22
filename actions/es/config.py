import os
import sys
import logging
from pathlib import Path
import json

from elasticsearch import AsyncElasticsearch

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


stage                   = os.getenv('STAGE'                 , 'dev'                                                     ) 
tf_cpp_min_log_level    = os.getenv('TF_CPP_MIN_LOG_LEVEL'  , '3'                                                       )
tf_embed_url            = os.getenv('TFHUB_EMBEDDING_URL'   , 'https://tfhub.dev/google/universal-sentence-encoder/4'   )
tfhub_cache_dir         = os.getenv('TFHUB_CACHE_DIR'       , '/var/tmp/tfhub_modules'                                  )
es_username             = os.getenv('ES_USERNAME'           , 'elastic'                                                 )
es_password             = os.getenv('ES_PASSWORD'           , 'changeme'                                                )
es_host                 = os.getenv('ES_HOST'               , 'http://localhost:9200/'                                  )
es_combined_index       = os.getenv('ES_COMBINED_INDEX'     , 'combined'                                                )
es_imitate              = os.getenv('ES_IMITATE'            , 'false'                                                   )
es_imitate              = es_imitate == 'true'

debug                   = os.getenv('DEBUG'         , 'false'   )
debug                   = debug == 'true'

es_search_size          = os.getenv('ES_SEARCH_SIZE', '10'      )
es_search_size          = int(es_search_size) if es_search_size.isdigit() else 10
try: es_search_size     = int(es_search_size)
except ValueError:
    logger.warning('ES_SEARCH_SIZE variable should be integer, using default value - 10')
    es_search_size = 10
es_cut_off              = os.getenv('ES_CUT_OFF'    , '0.4'     )
try: es_cut_off         = float(es_cut_off)
except ValueError:
    logger.warning('ES_CUT_OFF variable should be float, using default value - 0.4'     )
    es_cut_off = 0.4
es_top_n                = os.getenv('ES_TOP_N'      , '3'       )
try: es_top_n           = int(es_top_n)
except ValueError:
    logger.warning('ES_TOP_N variable should be integer, using default value - 3'       )
    es_cut_off = 3


if stage == 'dev':

    logger.info('----------------------------------------------')
    logger.info('Environment variables for DEV environment' )
    logger.info(f'- debug           = {debug}'                  )
    logger.info(f'- es_search_size  = {es_search_size}'         )
    logger.info(f'- es_cut_off      = {es_cut_off}'             )
    logger.info(f'- es_top_n        = {es_top_n}'               )
    logger.info('----------------------------------------------')
    
    
    _PATH = Path(__file__).parent.as_posix()

    # -------------------------------------------------------------
    # Define paths where data stored  
    PATH_DATA_ASKEXTENSION      = f'{_PATH}/data/askextension/2020-08-20/'
    PATH_DATA_UCIPM             = f'{_PATH}/data/uc-ipm/updated/'
    
    # Askexntension data
    ASKEXTENSION_QUESTION_URL   = 'https://ask2.extension.org/kb/faq.php?id='
    ASKEXTENSION_FILE_NAMES     = [f'{PATH_DATA_ASKEXTENSION}{f}'   for f in os.listdir(PATH_DATA_ASKEXTENSION  )]

    # UC IPM data
    UCIPM_FILE_NAMES            = [f'{PATH_DATA_UCIPM}{f}'          for f in os.listdir(PATH_DATA_UCIPM         )]
    # -------------------------------------------------------------

    # index mappings
    ES_COMBINED_MAPPING         = json.load(open(f'{_PATH}/data/mappings/combined_mapping.json'))


if not es_imitate:
    
    os.environ['TF_CPP_MIN_LOG_LEVEL']  = tf_cpp_min_log_level
    os.environ['TFHUB_CACHE_DIR']       = tfhub_cache_dir

    import tensorflow_hub as tf_hub
    
    logger.info('----------------------------------------------')
    logger.info('Elasticsearch configuration:')
    logger.info(f'- host                    = {es_host          }')
    logger.info(f'- username                = {es_username      }')
    logger.info(f'- password                = {es_password      }')
    logger.info(f'- tfhub_embedding_url     = {tf_embed_url     }')
    logger.info(f'- tfhub_cache_dir         = {tfhub_cache_dir  }')
    logger.info('----------------------------------------------')


    logger.info('----------------------------------------------')
    logger.info('Elasticsearch indexes:')
    logger.info(f'- combined index          = {es_combined_index    }')
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

