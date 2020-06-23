"""Create the elasticsearch index for scraped data"""
import json
from pathlib import Path
from elasticsearch.helpers import bulk

import setup_logger  # pylint: disable=unused-import

from actions import actions_config as ac


# Define the index
index_name = ac.ipmdata_index_name


INDEX_FILE = f"{Path(__file__).parents[1]}/data/{index_name}/index.json"
DATA_FILE = f"{Path(__file__).parents[1]}/data/{index_name}/{index_name}.json"

print("-----------------------------------------------------------")
print(f"index_name = {index_name}")
print(f"INDEX_FILE = {INDEX_FILE}")
print(f"DATA_FILE  = {DATA_FILE}")
print("-----------------------------------------------------------")


BATCH_SIZE = 1000
GPU_LIMIT = 0.5


def index_data():
    """Create the index"""
    if index_name == "posts":
        index_data_posts()
    elif index_name == "ipmdata":
        index_data_ipmdata()
    else:
        raise Exception(f"Not implemented for index_name = {index_name}")


def index_data_posts():
    """Create the index for stackoverflow posts"""
    print(f"Creating the index: {index_name}")
    ac.es_client.indices.delete(index=index_name, ignore=[404])

    with open(INDEX_FILE) as index_file:
        source = index_file.read().strip()
        ac.es_client.indices.create(index=index_name, body=source)

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

    ac.es_client.indices.refresh(index=index_name)
    print("Done indexing.")


def index_batch_posts(docs):
    """Index a batch of docs"""
    titles = [doc["title"] for doc in docs]
    title_vectors = ac.embed(titles).numpy()

    requests = []
    for i, doc in enumerate(docs):
        request = doc
        request["_op_type"] = "index"
        request["_index"] = index_name
        request["title_vector"] = title_vectors[i]
        requests.append(request)
    bulk(ac.es_client, requests)


def index_data_ipmdata():
    """Create the index for ipmdata"""
    print(f"Creating the index: {index_name}")
    ac.es_client.indices.delete(index=index_name, ignore=[404])

    with open(INDEX_FILE) as index_file:
        source = index_file.read().strip()
        ac.es_client.indices.create(index=index_name, body=source)

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

    ac.es_client.indices.refresh(index=index_name)
    print("Done indexing.")


def index_batch_ipmdata(docs):
    """Index a batch of docs"""

    # Update the docs prior to inserting:
    # - add embedding vectors
    pn_names = [doc["name"] for doc in docs]
    pn_name_vectors = ac.embed(pn_names).numpy()

    pn_descriptions = [doc["descriptionPestNote"] for doc in docs]
    pn_description_vectors = ac.embed(pn_descriptions).numpy()

    pn_life_cycles = [doc["life_cycle"] for doc in docs]
    pn_life_cycle_vectors = ac.embed(pn_life_cycles).numpy()

    pn_damages = [doc["damagePestNote"] for doc in docs]
    pn_damage_vectors = ac.embed(pn_damages).numpy()

    pn_managements = [doc["managementPestNote"] for doc in docs]
    pn_management_vectors = ac.embed(pn_managements).numpy()

    qt_contents = [doc["contentQuickTips"] for doc in docs]
    qt_content_vectors = ac.embed(qt_contents).numpy()

    # damage by itself does not work.
    # encode it together with name, description, life_cycle
    pn_ndl_damage = [
        doc["name"]
        + doc["descriptionPestNote"]
        + doc["life_cycle"]
        + doc["damagePestNote"]
        for doc in docs
    ]
    pn_ndl_damage_vectors = ac.embed(pn_ndl_damage).numpy()

    for (
        i,
        (
            pn_name_vector,
            pn_description_vector,
            pn_life_cycle_vector,
            pn_damage_vector,
            pn_management_vector,
            qt_content_vector,
            pn_ndl_damage_vector,
        ),
    ) in enumerate(
        zip(
            pn_name_vectors,
            pn_description_vectors,
            pn_life_cycle_vectors,
            pn_damage_vectors,
            pn_management_vectors,
            qt_content_vectors,
            pn_ndl_damage_vectors,
        )
    ):
        docs[i]["name_vector"] = pn_name_vector
        docs[i]["descriptionPestNote_vector"] = pn_description_vector
        docs[i]["life_cycle_vector"] = pn_life_cycle_vector
        docs[i]["damagePestNote_vector"] = pn_damage_vector
        docs[i]["managementPestNote_vector"] = pn_management_vector
        docs[i]["contentQuickTips_vector"] = qt_content_vector
        docs[i]["ndl_damage_vector"] = pn_ndl_damage_vector

        pn_images = docs[i]["imagePestNote"]
        if pn_images:
            captions = [pn_image["caption"] for pn_image in pn_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                docs[i]["imagePestNote"][j]["caption_vector"] = caption_vector

        qt_images = docs[i]["imageQuickTips"]
        if qt_images:
            captions = [qt_image["caption"] for qt_image in qt_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                docs[i]["imageQuickTips"][j]["caption_vector"] = caption_vector

    requests = []
    for i, doc in enumerate(docs):
        request = doc
        request["_op_type"] = "index"
        request["_index"] = index_name
        # request["descriptionPestNote_vector"] = pn_description_vectors[i]
        requests.append(request)
    bulk(ac.es_client, requests)


if __name__ == "__main__":
    index_data()
