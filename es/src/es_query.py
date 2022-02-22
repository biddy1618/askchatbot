import logging
import sys

import json
from typing import Dict
from collections import deque

import asyncio

import numpy as np
import pandas as pd
from elasticsearch.helpers import parallel_bulk

import config

# logging.basicConfig(stream = sys.stdout, level = logging.INFO)
logger = logging.getLogger(__name__)


def _get_embed(series: pd.Series) -> list:
    """Turn text data into embeddings using USE. 

    Args:
        series (pd.Series): Pandas series data type that holds text data.

    Returns:
        list: Embeddings in list data type.
    """    
    res = config.embed(series.tolist()).numpy()
    res = list(res)
    return res

def create_index(index_name: str, mapping: Dict) -> None:
    """Create an ES index.

    Args:
        index_name (str): Name of the index.
        mapping (Dict): Mapping of the index.
    """
    logger.info(f'Creating index {index_name}.')
    config.es_client.indices.delete(index = index_name, ignore = 404)        
    config.es_client.indices.create(index = index_name, ignore = 400, body = mapping)

def populate_index(path: str, index_name: str) -> None:
    """Populate an index from a CSV file.
    
    Args:
        path (str): The path to the CSV file.
        index_name (str): Name of the index to which documents should be written.
    """ 
    df = pd.read_json(path).replace({np.nan: None}).iloc[:10]
    df.loc[:, 'title-question-vector'] = _get_embed(df['title-question'])
    df = df.to_dict('records')

    logger.info(f'Writing {len(df)} documents to ES index {index_name}')
    deque(parallel_bulk(config.es_client, df, index = index_name), maxlen = 0)
    config.es_client.indices.refresh()
    success_insertions = config.es_client.cat.count(index_name, params = {"format": "json"})[0]['count']
    logger.info(f'Finished inserting. Succesful insertions: {success_insertions}')


async def es_query(
    query       : str, 
    index_name  : str = 'askextension', 
    vector_name : str = 'title-question-vector'
    ) -> None:
    """Actually perform ES query

    Args:
        query (str): text query
        index_name (str, optional): Name of the index. Defaults to 'askextension'.
        vector_name (str, optional): Name of the field to be compared. Defaults to 'title-question-vector'.
    """    
    query_vector = config.embed([query]).numpy()[0]
    cos = f'cosineSimilarity(params.query_vector, "{vector_name}") + 1.0'
    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {"source": cos, "params": {"query_vector": query_vector}
            }
        }
    }
    response = config.es_client.search(
        index   = index_name,
        query   = script_query,
        size    = 3,
        _source = {"includes": ["title", "question",]},
    )
    print(json.dumps(response['hits']['hits'], indent = 2))

async def main() -> None:
    """Main loop for ES query."""    
    while True:
        try:
            question = input('Enter your question: ')
            await es_query(question)
        except KeyboardInterrupt:
            return


if __name__ == '__main__':

    # if not config.es_client.indices.exists(index = config.ES_ASKEXTENSION_INDEX):
    create_index(config.ES_ASKEXTENSION_INDEX, config.ES_ASKEXTENSION_MAPPING)
    populate_index(config.ASKEXTENSION_FILE_RESULT, config.ES_ASKEXTENSION_INDEX)
    
    asyncio.run(main(), debug = True)
    print('Done.')

