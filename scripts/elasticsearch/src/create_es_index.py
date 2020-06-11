"""Create the elasticsearch index for scraped data"""
import json
from pathlib import Path
from elasticsearch.helpers import bulk

import setup_logger  # pylint: disable=unused-import

# from initialize import DATA_FILE, INDEX_NAME, INDEX_FILE, BATCH_SIZE
from actions import actions_config as ac


# Select the index to create by uncommenting one of these
# INDEX_NAME = 'posts'
INDEX_NAME = 'pestnotes'


INDEX_FILE = f"{Path(__file__).parents[1]}/data/{INDEX_NAME}/index.json"
DATA_FILE = f"{Path(__file__).parents[1]}/data/{INDEX_NAME}/{INDEX_NAME}.json"

print('-----------------------------------------------------------')
print(f"INDEX_NAME = {INDEX_NAME}")
print(f"INDEX_FILE = {INDEX_FILE}")
print(f"DATA_FILE  = {DATA_FILE}")
print('-----------------------------------------------------------')


BATCH_SIZE = 1000
GPU_LIMIT = 0.5


def index_data():
    """Create the index"""
    if INDEX_NAME == 'posts':
        index_data_posts()
    elif INDEX_NAME == 'pestnotes':
        index_data_pestnotes()
    else:
        raise Exception(f"Not implemented for INDEX_NAME = {INDEX_NAME}")


def index_data_posts():
    """Create the index for stackoverflow posts"""
    print(f"Creating the index: {INDEX_NAME}")
    ac.es_client.indices.delete(index=INDEX_NAME, ignore=[404])

    with open(INDEX_FILE) as index_file:
        source = index_file.read().strip()
        ac.es_client.indices.create(index=INDEX_NAME, body=source)

    docs = []
    count = 0

    with open(DATA_FILE) as data_file:
        for line in data_file:
            line = line.strip()

            doc = json.loads(line)
            if doc["type"] != "question":
                continue

            docs.append(doc)
            count += 1

            if count % BATCH_SIZE == 0:
                index_batch_posts(docs)
                docs = []
                print("Indexed {} documents.".format(count))

        if docs:
            index_batch_posts(docs)
            print("Indexed {} documents.".format(count))

    ac.es_client.indices.refresh(index=INDEX_NAME)
    print("Done indexing.")


def index_batch_posts(docs):
    """Index a batch of docs"""
    titles = [doc["title"] for doc in docs]
    title_vectors = ac.embed(titles).numpy()

    requests = []
    for i, doc in enumerate(docs):
        request = doc
        request["_op_type"] = "index"
        request["_index"] = INDEX_NAME
        request["title_vector"] = title_vectors[i]
        requests.append(request)
    bulk(ac.es_client, requests)


def index_data_pestnotes():
    """Create the index for pestnotes"""
    print(f"Creating the index: {INDEX_NAME}")
    ac.es_client.indices.delete(index=INDEX_NAME, ignore=[404])

    with open(INDEX_FILE) as index_file:
        source = index_file.read().strip()
        ac.es_client.indices.create(index=INDEX_NAME, body=source)

    docs_batch = []
    count = 0

    with open(DATA_FILE) as data_file:
        docs_all = json.load(data_file)
        docs_batch = []
        for doc in docs_all:

            docs_batch.append(doc)
            count += 1

            if count % BATCH_SIZE == 0:
                index_batch_pestnotes(docs_batch)
                docs_batch = []
                print("Indexed {} documents.".format(count))

        if docs_batch:
            index_batch_pestnotes(docs_batch)
            print("Indexed {} documents.".format(count))

    ac.es_client.indices.refresh(index=INDEX_NAME)
    print("Done indexing.")


def index_batch_pestnotes(docs):
    """Index a batch of docs"""
    descriptions = [doc["description"] for doc in docs]
    description_vectors = ac.embed(descriptions).numpy()

    requests = []
    for i, doc in enumerate(docs):
        request = doc
        request["_op_type"] = "index"
        request["_index"] = INDEX_NAME
        request["description_vector"] = description_vectors[i]
        requests.append(request)
    bulk(ac.es_client, requests)


if __name__ == "__main__":
    index_data()
