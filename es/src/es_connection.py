import json
import logging
import os
from typing import Dict

import numpy as np
import pandas as pd
from elasticsearch import Elasticsearch
from elasticsearch.helpers import parallel_bulk

from collections import deque

logging.basicConfig(filename="es.log", level=logging.INFO)


class EsManagement:
    def __init__(self):
        self.es_client = Elasticsearch(
            "localhost:9200",        )
        logging.info(self.es_client.ping())

        self.BATCH_SIZE = 500

    def create_index(self, index_name: str, mapping: Dict) -> None:
        """
        Create an ES index.
        :param index_name: Name of the index.
        :param mapping: Mapping of the index
        """
        logging.info(f"Creating index {index_name} with the following schema: {json.dumps(mapping, indent=2)}")
        self.es_client.indices.create(index=index_name, ignore=400, body=mapping)

    def populate_index(self, path: str, index_name: str) -> None:
        """
        Populate an index from a CSV file.
        :param path: The path to the CSV file.
        :param index_name: Name of the index to which documents should be written.
        """
        df = pd.read_json(path).replace({np.nan: None})
        logging.info(f"Writing {len(df.index)} documents to ES index {index_name}")
        df = df.to_dict('records')
        
        # self.es_client.indices.delete(index = 'test', ignore = 404)
        deque(parallel_bulk(self.es_client, df, index = index_name), maxlen = 0)
        self.es_client.indices.refresh()
        print('Done')
        print(self.es_client.cat.count(index_name, params={"format": "json"})[0]['count'])
