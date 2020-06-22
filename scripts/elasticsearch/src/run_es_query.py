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


def cosine_similarity_query(
    index_name,
    _source_query,
    query_vector,
    vector_name,
    nested=False,
    best_image="first",
    print_summary=False,
):
    """Does a query on cosine similarity between query_vector and the index field
    vector_name, and returns the list of hits
    
    _source_query = dict, defining what the query should return in the _source
    query_vector = the embedding vector we are sending
    vector_name = name of a dense_vector in the elasticsearch index
    """

    cos = f"cosineSimilarity(params.query_vector, '{vector_name}') + 1.0"

    if not nested:
        script_query = {
            "script_score": {
                "query": {"match_all": {}},
                "script": {"source": cos, "params": {"query_vector": query_vector},},
            }
        }
    else:
        ## https://stackoverflow.com/a/62354043/5480536
        path = vector_name[: vector_name.rfind(".")]
        script_query = {
            "nested": {
                "inner_hits": {},
                "path": path,
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

    response = ac.es_client.search(
        index=index_name,
        body={"size": ac.search_size, "query": script_query, "_source": _source_query,},
    )

    hits = response["hits"]["hits"]

    if print_summary and best_image == "first":
        # print it before filling out best image field
        print_hits(hits, title=vector_name)

    if best_image == "first":
        hits = set_first_image_as_best(hits)
    elif best_image == "caption":
        if vector_name in [
            "imagePestNote.caption_vector",
            "imageQuickTips.caption_vector",
        ]:
            # When scored on image caption, fist of the innerhits had the highest score
            for i, hit in enumerate(hits):
                hits[i]["best_image"] = None
                hits[i]["best_image"] = hit["inner_hits"][path]["hits"]["hits"][0][
                    "_source"
                ]
    else:
        raise Exception("Not implemented")

    if print_summary and best_image == "caption":
        # print it after filling out best image field
        print_hits(hits, title=vector_name)

    return hits


def set_first_image_as_best(hits):
    """When scored we do not know the best image. Just pick the first."""
    for i, hit in enumerate(hits):
        hits[i]["best_image"] = None
        if hit["_source"]["imagePestNote"]:
            hits[i]["best_image"] = hit["_source"]["imagePestNote"][0]

    return hits


def print_hits(hits, title=""):
    """print the hits & scores"""
    print("----------------------------------------------------------")
    print(title)
    # print("{} total hits.".format(response["hits"]["total"]["value"]))
    for hit in hits:
        print(
            f'{hit["_score"]}; '
            f'{hit["_source"]["name"]}; '
            f'image-caption={(hit.get("best_image", {}) or {}).get("caption")}'
        )


def handle_query():
    """Handles a single query"""
    index_name = INDEX_NAME
    query = input("Enter query: ")

    # create the embedding vector
    query_vector = ac.embed([query]).numpy()[0]

    # Define what the elasticsearch queries need to return in it's response
    _source_query = {
        "includes": [
            "name",
            "urlPestNote",
            "descriptionPestNote",
            "life_cycle",
            "damagePestNote",
            "managementPestNote",
            "imagePestNote",
            "urlQuickTip",
            "contentQuickTips",
            "imageQuickTips",
            "video",
        ]
    }

    pn_name_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "name_vector",
        nested=False,
        best_image="first",
        print_summary=True,
    )

    pn_description_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "descriptionPestNote_vector",
        nested=False,
        best_image="first",
        print_summary=True,
    )

    pn_life_cycle_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "life_cycle_vector",
        nested=False,
        best_image="first",
        print_summary=True,
    )

    qt_content_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "contentQuickTips_vector",
        nested=False,
        best_image="first",
        print_summary=True,
    )

    pn_caption_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "imagePestNote.caption_vector",
        nested=True,
        best_image="caption",
        print_summary=True,
    )

    qt_caption_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "imageQuickTips.caption_vector",
        nested=True,
        best_image="caption",
        print_summary=False,
    )

    ##########################################
    # Combine all hits and sort to max score #
    ##########################################

    hits = pn_name_hits
    for hit2 in (
        pn_description_hits
        + pn_life_cycle_hits
        + qt_content_hits
        + pn_caption_hits
        + qt_caption_hits
    ):
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


##### MAIN SCRIPT #####

if __name__ == "__main__":

    run_query_loop()

    print("Done.")
