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
es_askextension_index   = os.getenv('ES_ASKEXTENSION_INDEX' , 'askextension'                                            )
es_combined_index       = os.getenv('ES_COMBINED_INDEX'     , 'combined'                                                )
es_imitate              = os.getenv('ES_IMITATE'            , 'false'                                                   )
es_imitate              = es_imitate == 'true'

if stage == 'dev':

    logger.info('----------------------------------------------')
    logger.info('Environment variables are for DEV environment')
    logger.info('----------------------------------------------')
    
    
    _PATH = Path(__file__).parent.as_posix()

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

    # index mappings
    ES_ASKEXTENSION_MAPPING     = json.load(open(f'{_PATH}/data/mappings/askextension_mapping.json'))
    ES_COMBINED_VECTOR_MAPPING  = json.load(open(f'{_PATH}/data/mappings/combined_vector_mapping.json'))
    ES_COMBINED_MAPPING         = json.load(open(f'{_PATH}/data/mappings/combined_mapping.json'))

if not es_imitate:
    
    os.environ['TF_CPP_MIN_LOG_LEVEL']  = tf_cpp_min_log_level
    os.environ['TFHUB_CACHE_DIR']       = tfhub_cache_dir

    import tensorflow_hub as tf_hub
    
    logger.info('----------------------------------------------')
    logger.info('Elasticsearch configuration:')
    logger.info(f'- host                     = {es_host         }')
    logger.info(f'- username                 = {es_username     }')
    logger.info(f'- password                 = {es_password     }')
    logger.info(f'- tfhub_embedding_url      = {tf_embed_url    }')
    logger.info(f'- tfhub_cache_dir          = {tfhub_cache_dir }')
    logger.info('----------------------------------------------')


    logger.info('----------------------------------------------')
    logger.info('Elasticsearch indexes:')
    logger.info(f'- askextension index       = {es_askextension_index}')
    logger.info(f'- combined index           = {es_combined_index    }')
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

