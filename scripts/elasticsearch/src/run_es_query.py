"""Run elastic search queries from the command line"""
import time

import setup_logger  # pylint: disable=unused-import


# from initialize import DATA_FILE, INDEX_NAME, INDEX_FILE, BATCH_SIZE
from actions import actions_config as ac


# Select the index to create by uncommenting one of these
# INDEX_NAME = 'posts'
INDEX_NAME = "pestnotes"


def run_query_loop():
    """Run an infinite query loop. ^C to interrupt"""
    while True:
        try:
            handle_query()
        except KeyboardInterrupt:
            return


def handle_query():
    """Handles a single query"""
    query = input("Enter query: ")

    embedding_start = time.time()
    query_vector = ac.embed([query]).numpy()[0]
    embedding_time = time.time() - embedding_start

    if INDEX_NAME == "posts":
        cos = "cosineSimilarity(params.query_vector, doc['title_vector']) + 1.0"
        _source_query = {"includes": ["title", "body"]}
    elif INDEX_NAME == "pestnotes":
        script_query = {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_vector, doc['description_vector']) + 1.0",
                    "params": {"query_vector": query_vector},
                },
            }
        }
        _source_query = {"includes": ["name", "description"]}
    else:
        raise Exception(f"Not implemented for INDEX_NAME = {INDEX_NAME}")

    search_start = time.time()
    response = ac.es_client.search(
        index=INDEX_NAME,
        body={"size": ac.search_size, "query": script_query, "_source": _source_query,},
    )
    search_time = time.time() - search_start

    print()
    print("{} total hits.".format(response["hits"]["total"]["value"]))
    print("embedding time: {:.2f} ms".format(embedding_time * 1000))
    print("search time: {:.2f} ms".format(search_time * 1000))
    for hit in response["hits"]["hits"]:
        print("id: {}, score: {}".format(hit["_id"], hit["_score"]))
        print(hit["_source"])
        print()


##### MAIN SCRIPT #####

if __name__ == "__main__":

    run_query_loop()

    print("Done.")
