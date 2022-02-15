import logging
# import sys

import json
from typing import Dict

import asyncio

import numpy as np
import pandas as pd
from elasticsearch.helpers import parallel_bulk

from collections import deque

import config

# logging.basicConfig(stream = sys.stdout, level = logging.INFO)
logger = logging.getLogger(__name__)


def _get_embed(series: pd.Series) -> list:
    res = config.embed(series.tolist()).numpy()
    res = list(res)
    return res

def create_index(index_name: str, mapping: Dict) -> None:
    '''
    Create an ES index.
    :param index_name: Name of the index.
    :param mapping: Mapping of the index
    '''
    logger.info(f'Creating index {index_name} with the following schema: {json.dumps(mapping, indent=2)}')
    config.es_client.indices.delete(index = index_name, ignore = 404)        
    config.es_client.indices.create(index=index_name, ignore=400, body=mapping)

def populate_index(self, path: str, index_name: str) -> None:
    '''
    Populate an index from a CSV file.
    :param path: The path to the CSV file.
    :param index_name: Name of the index to which documents should be written.
    '''
    df = pd.read_json(path).replace({np.nan: None}).iloc[:10]
    df.loc[:, 'title-question-vector'] = _get_embed(df['title-question'])
    df = df.to_dict('records')

    logger.info(f'Writing {df.shape[0]} documents to ES index {index_name}')
    deque(parallel_bulk(self.es_client, df, index = index_name), maxlen = 0)
    config.es_client.indices.refresh()
    success_insertions = self.es_client.cat.count(index_name, params={"format": "json"})[0]['count']
    logger.info(f'Finished inserting. Succesful insertions: {success_insertions}')

def query():
    question = input('Enter your question: ')
    return question

async def es_query(query: str, index_name: str = 'askextension', vector_name: str = 'title-question-vector') -> None:

    query_vector = config.embed([query]).numpy()[0]
    cos = f"cosineSimilarity(params.query_vector, '{vector_name}') + 1.0"
    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {"source": cos, "params": {"query_vector": query_vector}
            }
        }
    }
    response = config.es_client.search(
        index=index_name,
        query=script_query,
        size = 3,
        _source={"includes": ["title", "question",]},
    )
    print(json.dumps(response['hits']['hits'], indent=2))

async def main():
    while True:
        try:
            question = query()
            await es_query(question)
        except KeyboardInterrupt:
            return


if __name__ == '__main__':

    if not config.es_client.indices.exists(index = config.askextension_index):
        create_index(config.askextension_index, config.askextension_mapping)
    
    asyncio.run(main(), debug = True)

