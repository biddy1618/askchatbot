"""Create the elasticsearch index for scraped data"""
import json
from pathlib import Path
from elasticsearch.helpers import bulk

import setup_logger  # pylint: disable=unused-import

# from initialize import DATA_FILE, INDEX_NAME, INDEX_FILE, BATCH_SIZE
from actions import actions_config as ac


# Define the index
INDEX_NAME = "ipmdata"


INDEX_FILE = f"{Path(__file__).parents[1]}/data/{INDEX_NAME}/index.json"
DATA_FILE = f"{Path(__file__).parents[1]}/data/{INDEX_NAME}/{INDEX_NAME}.json"

print("-----------------------------------------------------------")
print(f"INDEX_NAME = {INDEX_NAME}")
print(f"INDEX_FILE = {INDEX_FILE}")
print(f"DATA_FILE  = {DATA_FILE}")
print("-----------------------------------------------------------")


BATCH_SIZE = 1000
GPU_LIMIT = 0.5


def index_data():
    """Create the index"""
    if INDEX_NAME == "posts":
        index_data_posts()
    elif INDEX_NAME == "ipmdata":
        index_data_ipmdata()
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


def index_data_ipmdata():
    """Create the index for ipmdata"""
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
                index_batch_ipmdata(docs_batch)
                docs_batch = []
                print("Indexed {} documents.".format(count))

        if docs_batch:
            index_batch_ipmdata(docs_batch)
            print("Indexed {} documents.".format(count))

    ac.es_client.indices.refresh(index=INDEX_NAME)
    print("Done indexing.")


def index_batch_ipmdata(docs):
    """Index a batch of docs"""

    # Update the docs prior to inserting:
    # - add embedding vectors
    pn_names = [doc["name"] for doc in docs]
    pn_name_vectors = ac.embed(pn_names).numpy()
    pn_descriptions = [doc["descriptionPestNote"] for doc in docs]
    pn_description_vectors = ac.embed(pn_descriptions).numpy()
    for i, (pn_name_vector, pn_description_vector) in enumerate(
        zip(pn_name_vectors, pn_description_vectors)
    ):
        docs[i]["name_vector"] = pn_name_vector
        docs[i]["descriptionPestNote_vector"] = pn_description_vector
        pn_images = docs[i]["imagePestNote"]
        if pn_images:
            captions = [pn_image["caption"] for pn_image in pn_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                docs[i]["imagePestNote"][j]["caption_vector"] = caption_vector

    requests = []
    for i, doc in enumerate(docs):
        request = doc
        request["_op_type"] = "index"
        request["_index"] = INDEX_NAME
        # request["descriptionPestNote_vector"] = pn_description_vectors[i]
        requests.append(request)
    bulk(ac.es_client, requests)


if __name__ == "__main__":
    index_data()
