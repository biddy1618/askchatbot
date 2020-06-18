"""Run elastic search queries from the command line"""

import setup_logger  # pylint: disable=unused-import


# from initialize import DATA_FILE, INDEX_NAME, INDEX_FILE, BATCH_SIZE
from actions import actions_config as ac


# Select the index to create by uncommenting one of these
# INDEX_NAME = 'posts'
INDEX_NAME = "ipmdata"


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

    query_vector = ac.embed([query]).numpy()[0]

    # Define what the elasticsearch queries need to return in it's response
    # _source_query = {"includes": ["name", "imagePestNote"]}
    _source_query = {
        "includes": [
            "name",
            "urlPestNote",
            "descriptionPestNote",
            "damagePestNote",
            "managementPestNote",
            "imagePestNote",
            "urlQuickTip",
            "contentQuickTips",
            "imageQuickTips",
            "video",
        ]
    }

    #######################################
    # Score on descriptionPestNote_vector #
    #######################################

    cos = "cosineSimilarity(params.query_vector, 'descriptionPestNote_vector') + 1.0"

    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {"source": cos, "params": {"query_vector": query_vector},},
        }
    }

    response_pn_description = ac.es_client.search(
        index=INDEX_NAME,
        body={"size": ac.search_size, "query": script_query, "_source": _source_query,},
    )

    hits1 = response_pn_description["hits"]["hits"]
    # print without 'best image'
    print_hits(hits1, title="Best pestnote descriptions")

    # When scored on description, we do not know the best image. Just pick the first.
    for i, hit in enumerate(hits1):
        hits1[i]["best_image"] = None
        if hit["_source"]["imagePestNote"]:
            hits1[i]["best_image"] = hit["_source"]["imagePestNote"][0]

    #########################################
    # Score on imagePestNote.caption_vector #
    #########################################

    # How to query a vector:
    # - https://www.elastic.co/guide/en/elasticsearch/reference/7.x/query-dsl-script-score-query.html#vector-functions # pylint: disable=line-too-long
    # How to index & query nested objects:
    # - https://discuss.elastic.co/t/search-query-to-search-in-a-nested-type-object/211721
    # - https://stackoverflow.com/a/62354043/5480536
    # - https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-nested-query.html
    # - copy_to: https://stackoverflow.com/questions/40095499/elasticsearch-script-query-involving-root-and-nested-values

    cos = "cosineSimilarity(params.query_vector, 'imagePestNote.caption_vector') + 1.0"

    ## https://stackoverflow.com/a/62354043/5480536
    script_query = {
        "nested": {
            "inner_hits": {},
            "path": "imagePestNote",
            "score_mode": "max",
            "query": {
                "function_score": {
                    "script_score": {
                        "script": {
                            "source": cos,
                            "params": {"query_vector": query_vector},
                        },
                    }
                }
            },
        }
    }

    response_pn_image_caption = ac.es_client.search(
        index=INDEX_NAME,
        body={"size": ac.search_size, "query": script_query, "_source": _source_query,},
    )

    hits2 = response_pn_image_caption["hits"]["hits"]

    # When scored on image caption, the fist of the innerhits had the highest score
    for i, hit in enumerate(hits2):
        hits2[i]["best_image"] = None
        hits2[i]["best_image"] = hit["inner_hits"]["imagePestNote"]["hits"]["hits"][0][
            "_source"
        ]

    print_hits(hits2, title="Best image captions")

    ##########################################
    # Combine all hits and sort to max score #
    ##########################################

    # combine both queries
    # - merge info if same doc
    hits = hits1
    for hit2 in hits2:
        duplicate = False
        for i, hit in enumerate(hits):
            if hit2["_source"]["name"] == hit["_source"]["name"]:
                hits[i]["_score"] = max(hit["_score"], hit2["_score"])
                hits[i]["best_image"] = hit2["best_image"]
                duplicate = True
                break
        if not duplicate:
            hits.append(hit2)

    hits = sorted(hits, key=lambda h: h["_score"], reverse=True)

    print_hits(hits, title="Combined & sorted hits")


def print_hits(hits, title=""):
    """print the hits & scores"""
    print('----------------------------------------------------------')
    print(title)
    # print("{} total hits.".format(response["hits"]["total"]["value"]))
    for hit in hits:
        print(
            f'{hit["_score"]}; '
            f'{hit["_source"]["name"]}; '
            f'image-caption={hit.get("best_image",{}).get("caption")}'
        )


##### MAIN SCRIPT #####

if __name__ == "__main__":

    run_query_loop()

    print("Done.")
