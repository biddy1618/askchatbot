"""Custom Actions & Forms"""

import logging
import json
from typing import Any, Text, Dict, List, Union
from distutils.util import strtobool

from rasa_sdk import Action, Tracker
from rasa_sdk.forms import FormAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    ActionExecuted,
    EventType,
    UserUttered,
    UserUtteranceReverted,
    FollowupAction,
)

import inflect
import pandas as pd

from actions import actions_config as ac


logger = logging.getLogger(__name__)
inflecter = inflect.engine()

USE_AIOHTTP = False


# TODO: push into external file and add more items
PEST_NAME_MUST_BE_SINGULAR = ["mildew"]
PEST_NAME_MUST_BE_SINGULAR = [p.lower() for p in PEST_NAME_MUST_BE_SINGULAR]

pd.set_option("display.max_columns", 100)
pd.set_option("display.min_rows", 25)
pd.set_option("display.max_rows", 25)
pd.set_option("display.width", 1000)
# pd.set_option('display.max_colwidth', None)

# https://forum.rasa.com/t/trigger-a-story-or-intent-from-a-custom-action/13784/9?u=arjaan
def next_intent_events(next_intent: Text) -> List[Dict]:
    """Add next intent events, mimicking a prediction by NLU"""
    return [ActionExecuted("action_listen")] + [
        UserUttered(
            "/" + next_intent,
            {"intent": {"name": next_intent, "confidence": 1.0}, "entities": {}},
        )
    ]


def cosine_similarity_query(
    index_name,
    _source_query,
    query_vector,
    vector_name,
    nested=False,
    best_image="first",
    best_video="first",
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

    ##    if print_summary:
    ##        # print it before filling out best_image & best_video fields
    ##        print_hits(hits, title=vector_name)

    if best_image == "first":
        hits = set_first_image_as_best(hits)
    elif best_image == "caption":
        if vector_name in [
            "imagePestNote.caption_vector",
            "imageQuickTips.caption_vector",
            "imagesPestDiseaseItems.caption_vector",
            "imagesExoticPests.caption_vector",
        ]:
            # When scored on image caption, fist of the innerhits had the highest score
            for i, hit in enumerate(hits):
                hits[i]["best_image"] = None
                hits[i]["best_image"] = hit["inner_hits"][path]["hits"]["hits"][0][
                    "_source"
                ]
        else:
            raise Exception(
                f"Not implemented.\n "
                f"- best_image = {best_image}.\n"
                f"- vector_name = {vector_name}"
            )
    else:
        raise Exception(f"Not implemented. best_image = {best_image}")

    if best_video == "first":
        hits = set_first_video_as_best(hits)
    elif best_video == "title":
        if vector_name in [
            "video.videoTitle_vector",
        ]:
            # When scored on video, fist of the innerhits had the highest score
            for i, hit in enumerate(hits):
                hits[i]["best_video"] = None
                hits[i]["best_video"] = hit["inner_hits"][path]["hits"]["hits"][0][
                    "_source"
                ]
        else:
            raise Exception(
                f"Not implemented.\n "
                f"- best_video = {best_video}.\n"
                f"- vector_name = {vector_name}"
            )
    else:
        raise Exception(f"Not implemented. best_video = {best_video}")

    if print_summary:
        # print it after filling out best_image or best_video fields
        print_hits(hits, title=vector_name)

    return hits


def set_first_image_as_best(hits):
    """When scored we do not know the best image. Just pick the first if not yet set."""
    for hit in hits:
        if "best_image" not in hit.keys():
            hit["best_image"] = None

        if not hit["best_image"]:
            if hit["_source"]["imagePestNote"]:
                hit["best_image"] = hit["_source"]["imagePestNote"][0]
            elif hit["_source"]["imageQuickTips"]:
                hit["best_image"] = hit["_source"]["imageQuickTips"][0]
            elif hit["_source"]["imagesPestDiseaseItems"]:
                hit["best_image"] = hit["_source"]["imagesPestDiseaseItems"][0]
            elif hit["_source"]["imagesTurfPests"]:
                hit["best_image"] = hit["_source"]["imagesTurfPests"][0]
            elif hit["_source"]["imagesWeedItems"]:
                hit["best_image"] = hit["_source"]["imagesWeedItems"][0]
            elif hit["_source"]["imagesExoticPests"]:
                hit["best_image"] = hit["_source"]["imagesExoticPests"][0]

    return hits


def set_first_video_as_best(hits):
    """When scored we do not know the best video. Just pick the first if not yet set."""
    for hit in hits:
        if "best_video" not in hit.keys():
            hit["best_video"] = None

        if not hit["best_video"]:
            if hit["_source"]["video"]:
                hit["best_video"] = hit["_source"]["video"][0]

    return hits


def print_hits(hits, title=""):
    """print the hits & scores"""
    print("----------------------------------------------------------")
    print(title)
    # print("{} total hits.".format(response["hits"]["total"]["value"]))
    for hit in reversed(hits[:25]):

        if "_score_weighted" not in hit.keys():
            scores = f'score={hit.get("_score_max", 0.0):.3f}; '
        else:
            scores = (
                f'wght={hit.get("_score_weighted", 0.0):.3f}; '
                f'name={hit.get("_score_name",0.0):.3f}; '
                f'othr={hit.get("_score_other",0.0):.3f}; '
                f'capt={hit.get("_score_caption", 0.0):.3f}; '
                f'vdeo={hit.get("_score_video", 0.0):.3f}; '
                f'damg={hit.get("_score_damage", 0.0):.3f}; '
            )
        text = (
            # f'{hit["_id"]}; '
            f"{scores}"
            f'({hit["_source"]["doc_id"]}, {hit["_source"]["name"]}); '
            f'({hit["_source"]["ask_faq_id"]}, {hit["_source"]["ask_title"]}); '
            f'image-caption={(hit.get("best_image", {}) or {}).get("caption")}; '
            f'video-title={(hit.get("best_video", {}) or {}).get("videoTitle")}; '
        )

        pn_url = hit["_source"]["urlPestNote"]
        qt_url = hit["_source"]["urlQuickTip"]
        pdi_url = hit["_source"]["urlPestDiseaseItems"]
        tp_url = hit["_source"]["urlTurfPests"]
        wi_url = hit["_source"]["urlWeedItems"]
        ep_url = hit["_source"]["urlExoticPests"]
        ask_url = hit["_source"]["ask_url"]

        text = f"{text}URLS:"

        if qt_url:
            text = f"{text} [quick tip]({qt_url}),"
        if pn_url:
            text = f"{text} [pestnote]({pn_url}),"
        if pdi_url:
            text = f"{text} [pest disease item]({pdi_url}),"
        if tp_url:
            text = f"{text} [turf pest]({tp_url}),"
        if wi_url:
            text = f"{text} [weed item]({wi_url})"
        if ep_url:
            text = f"{text} [exotic pests]({ep_url})"
        if ask_url:
            text = f"{text} [askextension]({ask_url})"

        print(text)


async def do_es_queries(
    question,
    pest_name,
    pest_problem_description,
    pest_damage_description,
    index_name,
    print_summary=False,
):
    """Do the actual queries and return a dictionary with the lists of hits"""

    if index_name not in [
        "ipmdata",
        "ipmdata-dev",
        "ipmdata-dev-large-5",
        "ipm-and-ask-large-5",
    ]:
        raise Exception(f"Not implemented for index_name = {index_name}")

    # create the embedding vectors
    question_vector = None
    if question:
        question_vector = ac.embed([question]).numpy()[0]

    pest_name_vector = None
    if pest_name:
        pest_name_vector = ac.embed([pest_name]).numpy()[0]

    query_vector = None
    if pest_problem_description:
        query_vector = ac.embed([pest_problem_description]).numpy()[0]
    else:
        query_vector = question_vector

    damage_vector = None
    if pest_damage_description:
        damage_vector = ac.embed([pest_damage_description]).numpy()[0]

    # Define what the elasticsearch queries need to return in it's response
    _source_query = {
        "includes": [
            "doc_id",
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
            "urlPestDiseaseItems",
            "descriptionPestDiseaseItems",
            "identificationPestDiseaseItems",
            "life_cyclePestDiseaseItems",
            "damagePestDiseaseItems",
            "solutionsPestDiseaseItems",
            "imagesPestDiseaseItems",
            "other_headersPestDiseaseItems",
            "urlTurfPests",
            "textTurfPests",
            "imagesTurfPests",
            "urlWeedItems",
            "descriptionWeedItems",
            "imagesWeedItems",
            "urlExoticPests",
            "descriptionExoticPests",
            "damageExoticPests",
            "identificationExoticPests",
            "life_cycleExoticPests",
            "monitoringExoticPests",
            "managementExoticPests",
            "related_linksExoticPests",
            "imagesExoticPests",
            "ask_faq_id",
            "ask_url",
            "ask_title",
            "ask_created",
            "ask_updated",
            "ask_state",
            "ask_county",
            "ask_question",
            "ask_answer",
        ]
    }

    # TODO: Refactor this into loops
    es_ask_hits = {}
    es_name_hits = {}
    es_other_hits = {}
    es_damage_hits = {}
    es_caption_hits = {}
    es_video_hits = {}

    # all, except askextenstion
    es_name_hits["name_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "name_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    es_name_hits["pest_name_hits"] = []
    if pest_name:
        es_name_hits["pest_name_hits"] = cosine_similarity_query(
            index_name,
            _source_query,
            pest_name_vector,
            "name_vector",
            nested=False,
            best_image="first",
            best_video="first",
            print_summary=print_summary,
        )

    # ipmdata.json
    es_other_hits["pn_description_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "descriptionPestNote_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    es_other_hits["pn_life_cycle_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "life_cycle_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    es_other_hits["qt_content_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "contentQuickTips_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    es_damage_hits["pn_damage_hits"] = []
    if pest_damage_description:
        es_damage_hits["pn_damage_hits"] = cosine_similarity_query(
            index_name,
            _source_query,
            damage_vector,
            "damagePestNote_vector",
            nested=False,
            best_image="first",
            best_video="first",
            print_summary=print_summary,
        )

    # cleanedPestDiseaseItems.json
    es_other_hits["pdi_description_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "descriptionPestDiseaseItems_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    es_other_hits["pdi_identification_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "identificationPestDiseaseItems_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    es_other_hits["pdi_life_cycle_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "life_cyclePestDiseaseItems_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    es_damage_hits["pdi_damage_hits"] = []
    if pest_damage_description:
        es_damage_hits["pdi_damage_hits"] = cosine_similarity_query(
            index_name,
            _source_query,
            damage_vector,
            "damagePestDiseaseItems_vector",
            nested=False,
            best_image="first",
            best_video="first",
            print_summary=print_summary,
        )

    es_other_hits["pdi_solutions_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "solutionsPestDiseaseItems_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    # cleanedTurfPests.json
    es_other_hits["tp_text_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "textTurfPests_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    # cleanedWeedItems.json
    es_other_hits["wi_description_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "descriptionWeedItems_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    # cleanedExoticPests.json
    es_other_hits["ep_description_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "descriptionExoticPests_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    es_damage_hits["ep_damage_hits"] = []
    if pest_damage_description:
        es_damage_hits["ep_damage_hits"] = cosine_similarity_query(
            index_name,
            _source_query,
            damage_vector,
            "damageExoticPests_vector",
            nested=False,
            best_image="first",
            best_video="first",
            print_summary=print_summary,
        )

    es_other_hits["ep_identification_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "identificationExoticPests_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    es_other_hits["ep_life_cycle_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "life_cycleExoticPests_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    es_other_hits["ep_monitoring_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "monitoringExoticPests_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    es_other_hits["ep_management_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "managementExoticPests_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    # askextenstion
    es_ask_hits["ask_name_title_hits"] = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "ask_title_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    es_ask_hits["ask_pest_name_title_hits"] = []
    if pest_name:
        es_ask_hits["ask_pest_name_title_hits"] = cosine_similarity_query(
            index_name,
            _source_query,
            pest_name_vector,
            "ask_title_vector",
            nested=False,
            best_image="first",
            best_video="first",
            print_summary=print_summary,
        )

    es_ask_hits["ask_question_hits"] = []
    if question:
        es_ask_hits["ask_question_hits"] = cosine_similarity_query(
            index_name,
            _source_query,
            question_vector,
            "ask_title_question_vector",
            nested=False,
            best_image="first",
            best_video="first",
            print_summary=print_summary,
        )

    es_ask_hits["ask_damage_hits"] = []
    if pest_damage_description:
        es_ask_hits["ask_damage_hits"] = cosine_similarity_query(
            index_name,
            _source_query,
            damage_vector,
            "ask_title_question_vector",
            nested=False,
            best_image="first",
            best_video="first",
            print_summary=print_summary,
        )

    do_nested = True
    # image captions might not be helping in the rating of the docs
    do_captions = True
    do_videos = True

    es_caption_hits["pn_caption_hits"] = []
    es_caption_hits["qt_caption_hits"] = []
    es_video_hits["video_link_hits"] = []
    es_caption_hits["pdi_caption_hits"] = []
    es_other_hits["pdi_header_hits"] = []
    es_other_hits["pdi_text_hits"] = []
    es_other_hits["ep_text_hits"] = []
    es_caption_hits["ep_caption_hits"] = []
    es_ask_hits["ask_response_hits"] = []
    if not do_nested:
        print("SKIPPING SEARCH IN NESTED FIELDS")
    if do_nested:
        # ipmdata.json
        if do_captions:
            es_caption_hits["pn_caption_hits"] = cosine_similarity_query(
                index_name,
                _source_query,
                query_vector,
                "imagePestNote.caption_vector",
                nested=True,
                best_image="caption",
                best_video="first",
                print_summary=print_summary,
            )
            if pest_name:
                es_caption_hits["pn_caption_hits"] = es_caption_hits[
                    "pn_caption_hits"
                ] + cosine_similarity_query(
                    index_name,
                    _source_query,
                    pest_name_vector,
                    "imagePestNote.caption_vector",
                    nested=True,
                    best_image="caption",
                    best_video="first",
                    print_summary=print_summary,
                )

            es_caption_hits["qt_caption_hits"] = cosine_similarity_query(
                index_name,
                _source_query,
                query_vector,
                "imageQuickTips.caption_vector",
                nested=True,
                best_image="caption",
                best_video="first",
                print_summary=print_summary,
            )
            if pest_name:
                es_caption_hits["qt_caption_hits"] = es_caption_hits[
                    "qt_caption_hits"
                ] + cosine_similarity_query(
                    index_name,
                    _source_query,
                    pest_name_vector,
                    "imageQuickTips.caption_vector",
                    nested=True,
                    best_image="caption",
                    best_video="first",
                    print_summary=print_summary,
                )

        if do_videos:
            es_video_hits["video_link_hits"] = cosine_similarity_query(
                index_name,
                _source_query,
                query_vector,
                "video.videoTitle_vector",
                nested=True,
                best_image="first",
                best_video="title",
                print_summary=print_summary,
            )
            if pest_name:
                es_video_hits["video_link_hits"] = es_video_hits[
                    "video_link_hits"
                ] + cosine_similarity_query(
                    index_name,
                    _source_query,
                    pest_name_vector,
                    "video.videoTitle_vector",
                    nested=True,
                    best_image="first",
                    best_video="title",
                    print_summary=print_summary,
                )

        # cleanedPestDiseaseItems.json
        if do_captions:
            es_caption_hits["pdi_caption_hits"] = cosine_similarity_query(
                index_name,
                _source_query,
                query_vector,
                "imagesPestDiseaseItems.caption_vector",
                nested=True,
                best_image="caption",
                best_video="first",
                print_summary=print_summary,
            )
            if pest_name:
                es_caption_hits["pdi_caption_hits"] = es_caption_hits[
                    "pdi_caption_hits"
                ] + cosine_similarity_query(
                    index_name,
                    _source_query,
                    pest_name_vector,
                    "imagesPestDiseaseItems.caption_vector",
                    nested=True,
                    best_image="caption",
                    best_video="first",
                    print_summary=print_summary,
                )

        es_other_hits["pdi_header_hits"] = cosine_similarity_query(
            index_name,
            _source_query,
            query_vector,
            "other_headersPestDiseaseItems.header_vector",
            nested=True,
            best_image="first",
            best_video="first",
            print_summary=print_summary,
        )
        if pest_name:
            es_other_hits["pdi_header_hits"] = es_other_hits[
                "pdi_header_hits"
            ] + cosine_similarity_query(
                index_name,
                _source_query,
                pest_name_vector,
                "other_headersPestDiseaseItems.header_vector",
                nested=True,
                best_image="first",
                best_video="first",
                print_summary=print_summary,
            )

        es_other_hits["ep_text_hits"] = cosine_similarity_query(
            index_name,
            _source_query,
            query_vector,
            "other_headersPestDiseaseItems.text_vector",
            nested=True,
            best_image="first",
            best_video="first",
            print_summary=print_summary,
        )
        if pest_name:
            es_other_hits["ep_text_hits"] = es_other_hits[
                "ep_text_hits"
            ] + cosine_similarity_query(
                index_name,
                _source_query,
                pest_name_vector,
                "other_headersPestDiseaseItems.text_vector",
                nested=True,
                best_image="first",
                best_video="first",
                print_summary=print_summary,
            )

        # cleanedExoticPests.json
        ep_text_hits = cosine_similarity_query(
            index_name,
            _source_query,
            query_vector,
            "related_linksExoticPests.text_vector",
            nested=True,
            best_image="first",
            best_video="first",
            print_summary=print_summary,
        )
        if pest_name:
            ep_text_hits = ep_text_hits + cosine_similarity_query(
                index_name,
                _source_query,
                pest_name_vector,
                "related_linksExoticPests.text_vector",
                nested=True,
                best_image="first",
                best_video="first",
                print_summary=print_summary,
            )

        if do_captions:
            es_caption_hits["ep_caption_hits"] = cosine_similarity_query(
                index_name,
                _source_query,
                query_vector,
                "imagesExoticPests.caption_vector",
                nested=True,
                best_image="caption",
                best_video="first",
                print_summary=print_summary,
            )
            if pest_name:
                es_caption_hits["ep_caption_hits"] = es_caption_hits[
                    "ep_caption_hits"
                ] + cosine_similarity_query(
                    index_name,
                    _source_query,
                    pest_name_vector,
                    "imagesExoticPests.caption_vector",
                    nested=True,
                    best_image="caption",
                    best_video="first",
                    print_summary=print_summary,
                )

        es_ask_hits["ask_response_hits"] = []
        if question:
            es_ask_hits["ask_response_hits"] = cosine_similarity_query(
                index_name,
                _source_query,
                question_vector,
                "ask_answer.response_vector",
                nested=True,
                best_image="first",
                best_video="first",
                print_summary=print_summary,
            )

    return (
        es_ask_hits,
        es_name_hits,
        es_other_hits,
        es_damage_hits,
        es_caption_hits,
        es_video_hits,
    )


async def merge_and_score_hits(
    es_ask_hits,
    es_name_hits,
    es_other_hits,
    es_damage_hits,
    es_caption_hits,
    es_video_hits,
    pest_damage_description,
):
    """Combine all hits and score per category"""

    ####################################
    # askextension docs
    # Do not use categories, just max it accross all scores
    #
    hits = []
    for hit2 in (
        es_ask_hits["ask_name_title_hits"]
        + es_ask_hits["ask_pest_name_title_hits"]
        + es_ask_hits["ask_question_hits"]
        + es_ask_hits["ask_damage_hits"]
        + es_ask_hits["ask_response_hits"]
    ):
        hit2["_score_max"] = hit2.get("_score", 0.0)
        duplicate = False
        for hit in hits:
            if hit2["_source"]["doc_id"] == hit["_source"]["doc_id"]:
                hit["_score_max"] = max(hit.get("_score_max", 0.0), hit2["_score"])
                duplicate = True
                break
        if not duplicate:
            hits.append(hit2)

    # this sort is not needed, just for debugging
    if len(hits) > 0:
        hits = sorted(hits, key=lambda h: h["_score_max"], reverse=True)
    hits_ask = hits

    ############################################################
    # ipmdata
    hits = []

    # The name searches
    for hit2 in es_name_hits["name_hits"] + es_name_hits["pest_name_hits"]:
        hit2["_score_name"] = hit2.get("_score", 0.0)
        duplicate = False
        for hit in hits:
            if hit2["_source"]["doc_id"] == hit["_source"]["doc_id"]:
                hit["_score_name"] = max(hit.get("_score_name", 0.0), hit2["_score"])
                duplicate = True
                break
        if not duplicate:
            hits.append(hit2)

    # first the non-image-caption & non-video-title searches
    for hit in hits:
        hit["_score_other"] = 0.0
    for hit2 in (
        es_other_hits["pn_description_hits"]
        + es_other_hits["pn_life_cycle_hits"]
        + es_other_hits["qt_content_hits"]
        + es_other_hits["pdi_description_hits"]
        + es_other_hits["pdi_identification_hits"]
        + es_other_hits["pdi_life_cycle_hits"]
        + es_other_hits["pdi_solutions_hits"]
        + es_other_hits["pdi_header_hits"]
        + es_other_hits["pdi_text_hits"]
        + es_other_hits["tp_text_hits"]
        + es_other_hits["wi_description_hits"]
        + es_other_hits["ep_description_hits"]
        + es_other_hits["ep_identification_hits"]
        + es_other_hits["ep_life_cycle_hits"]
        + es_other_hits["ep_monitoring_hits"]
        + es_other_hits["ep_management_hits"]
        + es_other_hits["ep_text_hits"]
    ):
        hit2["_score_other"] = hit2.get("_score", 0.0)
        duplicate = False
        for hit in hits:
            if hit2["_source"]["doc_id"] == hit["_source"]["doc_id"]:
                hit["_score_other"] = max(hit.get("_score_other", 0.0), hit2["_score"])
                duplicate = True
                break
        if not duplicate:
            hits.append(hit2)

    # then the image caption searches
    for hit in hits:
        hit["_score_caption"] = 0.0
    for hit2 in (
        es_caption_hits["pn_caption_hits"]
        + es_caption_hits["qt_caption_hits"]
        + es_caption_hits["pdi_caption_hits"]
        + es_caption_hits["ep_caption_hits"]
    ):
        hit2["_score_caption"] = hit2.get("_score", 0.0)
        duplicate = False
        for hit in hits:
            if hit2["_source"]["doc_id"] == hit["_source"]["doc_id"]:
                hit["_score_caption"] = max(
                    hit.get("_score_caption", 0.0), hit2.get("_score", 0.0)
                )
                hit["best_image"] = hit2["best_image"]
                duplicate = True
                break
        if not duplicate:
            hits.append(hit2)

    # then the video-title searches
    for hit in hits:
        hit["_score_video"] = 0.0
    for hit2 in es_video_hits["video_link_hits"]:
        hit2["_score_video"] = hit2.get("_score", 0.0)
        duplicate = False
        for hit in hits:
            if hit2["_source"]["doc_id"] == hit["_source"]["doc_id"]:
                hit["_score_video"] = max(
                    hit.get("_score_video", 0.0), hit2.get("_score", 0.0)
                )
                hit["best_video"] = hit2["best_video"]
                duplicate = True
                break
        if not duplicate:
            hits.append(hit2)

    # Scores based on damage vector
    for hit in hits:
        hit["_score_damage"] = 0.0
    if pest_damage_description:
        for hit2 in (
            es_damage_hits["pn_damage_hits"]
            + es_damage_hits["pdi_damage_hits"]
            + es_damage_hits["ep_damage_hits"]
        ):
            hit2["_score_damage"] = hit2.get("_score", 0.0)
            duplicate = False
            for hit in hits:
                if hit2["_source"]["doc_id"] == hit["_source"]["doc_id"]:
                    hit["_score_damage"] = max(
                        hit.get("_score_damage", 0.0), hit2.get("_score", 0.0)
                    )
                    duplicate = True
                    break
            if not duplicate:
                hits.append(hit2)

    # this sort is not needed, just for debugging
    if len(hits) > 0:
        hits = sorted(hits, key=lambda h: h["_score"], reverse=True)
    hits_ipm = hits

    return hits_ask, hits_ipm


async def weight_score(hits_ask, hits_ipm):
    """Apply weighting"""
    #######################################################################
    # For searches in the askextension data, we do not weigh. Already maxed

    if len(hits_ask) > 0:
        hits_ask = sorted(hits_ask, key=lambda h: h["_score_max"], reverse=True)

    #######################################################################
    if len(hits_ipm) > 0:
        for hit in hits_ipm:
            score_name = hit.get("_score_name", 0.0)

            score_other = max(
                hit.get("_score_other", 0.0),
                hit.get("_score_caption", 0.0),
                hit.get("_score_video", 0.0),
            )

            score_damage = hit.get("_score_damage", 0.0)

            w = [0.9, 0.05, 0.05]

            if score_damage < 1.0:
                w[0] += 0.5 * w[2]
                w[1] += 0.5 * w[2]
                w[2] = 0.0

            hit["_score_weighted"] = (
                w[0] * score_name + w[1] * score_other + w[2] * score_damage
            )

        # Sort to weighted score
        hits_ipm = sorted(hits_ipm, key=lambda h: h["_score_weighted"], reverse=True)

    # Do not filter on threshold. Leave this up to the caller
    return hits_ask, hits_ipm


async def handle_es_query(
    question,
    pest_name,
    pest_problem_description,
    pest_damage_description,
    index_name,
    print_summary=False,
):
    """Handles an elastic search query"""

    (
        es_ask_hits,
        es_name_hits,
        es_other_hits,
        es_damage_hits,
        es_caption_hits,
        es_video_hits,
    ) = await do_es_queries(
        question,
        pest_name,
        pest_problem_description,
        pest_damage_description,
        index_name,
        print_summary,
    )

    hits_ask, hits_ipm = await merge_and_score_hits(
        es_ask_hits,
        es_name_hits,
        es_other_hits,
        es_damage_hits,
        es_caption_hits,
        es_video_hits,
        pest_damage_description,
    )

    hits_ask, hits_ipm = await weight_score(hits_ask, hits_ipm)

    if print_summary:
        print_hits(hits_ask, title="Combined, Weighted & sorted hits_ask")
        print_hits(hits_ipm, title="Combined, Weighted & sorted hits_ipm")

    return hits_ask, hits_ipm


class ActionHi(Action):
    """Get the conversation going"""

    def name(self) -> Text:
        return "action_hi"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        shown_privacypolicy = tracker.get_slot("shown_privacypolicy")
        said_hi = tracker.get_slot("said_hi")
        explained_ipm = tracker.get_slot("explained_ipm")

        if not said_hi:
            dispatcher.utter_message(template="utter_hi")
            dispatcher.utter_message(template="utter_summarize_skills")

        if not shown_privacypolicy:
            dispatcher.utter_message(template="utter_inform_privacypolicy")

        buttons = []

        buttons.append(
            {"title": "I have a question", "payload": "/intent_i_have_a_question",}
        )

        buttons.append(
            {"title": "I have a pest problem", "payload": "/intent_i_have_a_pest",}
        )

        if not explained_ipm:
            buttons.append(
                {"title": "Explain IPM", "payload": "/intent_explain_ipm",}
            )

        if said_hi:
            buttons.append(
                {"title": "Goodbye", "payload": "/intent_bye",}
            )

        buttons.append(
            {"title": "Something else", "payload": "/intent_out_of_scope",}
        )

        dispatcher.utter_message(
            text="Please select one of these options", buttons=buttons
        )

        events = reset_slots_from_previous_forms()
        return events


class ActionExplainIPM(Action):
    """Explain IPM"""

    def name(self) -> Text:
        return "action_explain_ipm"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        dispatcher.utter_message(template="utter_explain_ipm")
        return [SlotSet("explained_ipm", True)]


class ActionKickoffAnotherIHaveAPestIntent(Action):
    """Kickoff another intent_i_have_a_pest, after cleaning out the Tracker"""

    def name(self) -> Text:
        return "action_kickoff_intent_i_have_a_pest"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        events = reset_slots_from_previous_forms()
        events.extend(next_intent_events("intent_i_have_a_pest"))
        return events


class ActionKickoffAnotherIHaveAQuestionIntent(Action):
    """Kickoff another intent_i_have_a_question, after cleaning out the Tracker"""

    def name(self) -> Text:
        return "action_kickoff_intent_i_have_a_question"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        events = reset_slots_from_previous_forms()
        events.extend(next_intent_events("intent_i_have_a_question"))
        return events


class ActionAskHandoffToExpert(Action):
    """Asks if user wants to ask the question to an expert/human"""

    def name(self) -> Text:
        return "action_ask_handoff_to_expert"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        dispatcher.utter_message(template="utter_do_you_want_to_ask_a_human_expert")


class FormQueryKnowledgeBase(FormAction):
    """Query the Knowledge Base"""

    def name(self) -> Text:
        return "form_query_knowledge_base"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""

        def how_did_we_get_here(tracker: Tracker) -> Text:
            """Find out if we came here because of a question or a pest problem.
            Do this by looking at all the events, and find the latest one that could have
            triggered the calling of this form.
            """
            df = pd.DataFrame(tracker.events)
            loc_pest = 0
            loc_question = 0
            if "/intent_i_have_a_pest" in df["text"].values:
                loc_pest = df[df["text"] == "/intent_i_have_a_pest"].index.values[-1]
            if "/intent_i_have_a_question" in df["text"].values:
                loc_question = df[
                    df["text"] == "/intent_i_have_a_question"
                ].index.values[-1]

            if loc_pest > loc_question:
                return "/intent_i_have_a_pest"

            return "/intent_i_have_a_question"

        if how_did_we_get_here(tracker) == "/intent_i_have_a_pest":
            slots = ["pest_problem_description"]

            if tracker.get_slot("pest_causes_damage") != "no":
                slots.extend(
                    ["pest_causes_damage", "pest_damage_description",]
                )
        else:
            slots = ["question"]

        return slots

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""

        return {
            "question": [
                self.from_text(
                    not_intent=["intent_garbage_inputs", "intent_configure_bot"]
                )
            ],
            "pest_problem_description": [
                self.from_text(
                    not_intent=["intent_garbage_inputs", "intent_configure_bot"]
                )
            ],
            "pest_causes_damage": [
                self.from_intent(value="yes", intent="intent_yes"),
                self.from_intent(value="no", intent="intent_no"),
            ],
            "pest_damage_description": [
                self.from_text(
                    not_intent=["intent_garbage_inputs", "intent_configure_bot"]
                )
            ],
        }

    @staticmethod
    def pest_name_plural(pest_name):
        """Returns the pest_name in plural form"""
        pest_singular = inflecter.singular_noun(pest_name)
        if not pest_singular:
            pest_singular = pest_name
        pest_plural = inflecter.plural_noun(pest_singular)
        return pest_plural

    @staticmethod
    def keep_pest_name_singular(name):
        """Returns True if the pest name only makes sense in singular form"""
        name_lower = name.lower()
        for key in PEST_NAME_MUST_BE_SINGULAR:
            if key in name_lower:
                return True
        return False

    async def validate_pest_problem_description(
        self,
        value: Text,
        _dispatcher: CollectingDispatcher,
        tracker: Tracker,
        _domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Once pest problem is described:
        
        If no pest name was extracted:
          -> do not ask for damage
          -> set the damage equal to the description
          
        If a pest name was extracted:
          -> build damage question to ask, using the pest name in plural form
          """

        # see if a pest name was extracted from the problem description
        pest_name = tracker.get_slot("pest_name")

        if not pest_name:
            # question = "Is there any damage?"
            return {
                "pest_problem_description": value,
                "pest_causes_damage": "did-not-ask",
                "pest_damage_description": value,
            }

        if self.keep_pest_name_singular(pest_name):
            question = f"Is the {pest_name.lower()} causing any damage?"
            return {
                "pest_problem_description": value,
                "cause_damage_question": question,
            }

        pest_plural = self.pest_name_plural(pest_name)
        question = f"Are the {pest_plural.lower()} causing any damage?"
        return {"pest_problem_description": value, "cause_damage_question": question}

    def summarize_hits(self, hits_ask, hits_ipm, tracker) -> list:
        """Create a list of dictionaries, where each dictionary contains those items we
        want to use when presenting the hits in a conversational manner to the user."""
        pests_summaries = []
        if not hits_ask and not hits_ipm:
            return pests_summaries

        for i, hit in enumerate(hits_ask[: min(3, len(hits_ask))]):
            hit_summary = {}
            score = hit["_score_max"]
            hit_summary["message"] = self.create_text_for_pest(
                i, hit, score, tracker, "From askextension data:"
            )
            pests_summaries.append(hit_summary)

        for i, hit in enumerate(hits_ipm[: min(3, len(hits_ipm))]):
            hit_summary = {}
            score = hit["_score_weighted"]
            hit_summary["message"] = self.create_text_for_pest(
                i, hit, score, tracker, "From IPM data:"
            )
            pests_summaries.append(hit_summary)

        return pests_summaries

    @staticmethod
    def create_text_for_pest(i, hit, score, tracker, header) -> str:
        """Prepares a message for the user"""
        name = hit["_source"]["name"]
        ask_title = hit["_source"]["ask_title"]
        pn_url = hit["_source"]["urlPestNote"]
        qt_url = hit["_source"]["urlQuickTip"]
        pdi_url = hit["_source"]["urlPestDiseaseItems"]
        tp_url = hit["_source"]["urlTurfPests"]
        wi_url = hit["_source"]["urlWeedItems"]
        ep_url = hit["_source"]["urlExoticPests"]
        ask_url = hit["_source"]["ask_url"]
        # pn_image = None
        # if hit["best_image"]:
        #    pn_image = hit["best_image"]["src"]
        #    pn_image_caption = hit["best_image"]["caption"]

        # if pn_image:
        #    text = f"{name}: {pn_image_caption}\n"
        # else:
        #    text = f"{name}\n"

        #
        # BE VERY CAREFUL:
        # \n\n does not work. It does not wrap the sentences
        #

        # list symbol
        # Do not use:
        # "-", " >", "\t", "+"
        # s = " o"  # this works, but not so nice
        s = r"\-"

        # divider line
        # Do not use:
        # divider = "======================================"
        # divider = "\  \n"
        divider = r"\-"
        divider_long = r"\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-"

        text = ""
        if i == 0:
            text = f"{divider_long}\n{header}\n"

        if name:
            text = f"{text}\n({score})**{name}**\n"
        if ask_title:
            text = f"{text}\n({score})**{ask_title}**\n"

        if qt_url:
            text = f"{text}{s} _[quick tip]({qt_url})_\n"
        if pn_url:
            text = f"{text}{s} _[pestnote]({pn_url})_\n"
        if pdi_url:
            text = f"{text}{s} _[pest disease item]({pdi_url})_\n"
        if tp_url:
            text = f"{text}{s} _[turf pest]({tp_url})_\n"
        if wi_url:
            text = f"{text}{s} _[weed item]({wi_url})_\n"
        if ep_url:
            text = f"{text}{s} _[exotic pests]({ep_url})_\n"
        if ask_url:
            text = f"{text}{s} _[askextension]({ask_url})_\n"

        if hit["best_video"]:
            video_title = hit["best_video"]["videoTitle"]
            video_link = hit["best_video"]["videoLink"]
            text = f"{text}{s} _[video: '{video_title}']({video_link})_\n"

        if tracker.get_slot("bot_config_debug"):
            ##text = (
            ##    f'{text}{s} _weighted score  ={hit.get("_score_weighted", 0.0):.3f}_\n'
            ##)
            ##text = f'{text}{s} _score for name  ={hit.get("_score_name",0.0):.3f}_\n'
            ##text = f'{text}{s} _score for other ={hit.get("_score_other",0.0):.3f}_\n'
            ##text = (
            ##    f'{text}{s} _score for caption={hit.get("_score_caption", 0.0):.3f}_\n'
            ##)
            ##text = (
            ##    f'{text}{s} _score for video   ={hit.get("_score_video", 0.0):.3f}_\n'
            ##)
            ##text = (
            ##    f'{text}{s} _score for damage  ={hit.get("_score_damage", 0.0):.3f}_\n'
            ##)
            if score < tracker.get_slot("bot_config_score_threshold"):
                text = (
                    f"{text}{s} _Below score threshold of "
                    f"{tracker.get_slot('bot_config_score_threshold'):.2f}_\n"
                )
            ##            else:
            ##                text = (
            ##                    f"{text}{s} _Above score threshold of "
            ##                f"{tracker.get_slot('bot_config_score_threshold'):.2f}_\n"
            ##                )

            # Note that \n\n is not working
            text = f"{text}{divider}\n"
        return text

    async def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""

        pest_name = tracker.get_slot("pest_name")
        pest_problem_description = tracker.get_slot("pest_problem_description")
        pest_causes_damage = tracker.get_slot("pest_causes_damage")
        pest_damage_description = None
        if pest_causes_damage != "no":
            pest_damage_description = tracker.get_slot("pest_damage_description")
        question = tracker.get_slot("question")

        if ac.do_the_queries:
            hits_ask, hits_ipm = await handle_es_query(
                question,
                pest_name,
                pest_problem_description,
                pest_damage_description,
                ac.ipmdata_index_name,
                print_summary=False,
            )
        else:
            message = "Not doing an actual elastic search query."
            dispatcher.utter_message(message)
            hits_ask = []
            hits_ipm = []

        pests_summaries = self.summarize_hits(hits_ask, hits_ipm, tracker)
        return [SlotSet("pests_summaries", pests_summaries)]


class FormPresentHits(FormAction):
    """Present the hits to the user"""

    def name(self) -> Text:
        return "form_present_hits"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""

        slots = ["pests_summaries", "pest_summary_and_did_this_help"]

        return slots

    async def validate_pests_summaries(
        self,
        value: Text,
        _dispatcher: CollectingDispatcher,
        tracker: Tracker,
        _domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """The slot pests_summaries is set before form activation, so we use this method
        to initialize the presentation logic."""

        pests_summaries_index = -1
        (
            pest_summaries,
            pests_summaries_index,
        ) = await self.get_multiple_pest_summaries(pests_summaries_index, tracker)

        if len(pest_summaries) > 0:
            # we have more to present
            text = ""
            for pest_summary in pest_summaries:
                text = f"{text}{pest_summary}"

            return {
                "pest_summary_and_did_this_help": None,
                "pests_summaries_index": pests_summaries_index,
                "pest_summary": text,
            }

        # we have nothing to present
        return {
            "pests_summaries": value,
            "pest_summary_and_did_this_help": "no",
        }

    async def validate_pest_summary_and_did_this_help(
        self,
        value: Text,
        _dispatcher: CollectingDispatcher,
        tracker: Tracker,
        _domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """After presenting a result and asking if it helps."""

        # helpful, stop here
        if value == "yes":
            return {"pest_summary_and_did_this_help": value}

        # not helpful, show more if we can
        pests_summaries_index = tracker.get_slot("pests_summaries_index")
        (
            pest_summaries,
            pests_summaries_index,
        ) = await self.get_multiple_pest_summaries(pests_summaries_index, tracker)

        if len(pest_summaries) > 0:
            # we have more to present
            text = ""
            for pest_summary in pest_summaries:
                text = f"{text}{pest_summary}"

            return {
                "pest_summary_and_did_this_help": None,
                "pests_summaries_index": pests_summaries_index,
                "pest_summary": text,
            }

        # we have nothing more to present
        return {"pest_summary_and_did_this_help": value}

    async def get_multiple_pest_summaries(
        self, pests_summaries_index, tracker, max_pests=10
    ):
        """Show 6 results at a time, up to max_pests"""
        pest_summaries = []
        for _i in range(6):
            pest_summary = None
            if pests_summaries_index < max_pests - 1:
                pests_summaries_index = pests_summaries_index + 1
                pest_summary = self.pest_summary(pests_summaries_index, tracker)

            if pest_summary:
                pest_summaries.append(pest_summary)
            else:
                break
        return pest_summaries, pests_summaries_index

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""

        return {
            "pest_summary_and_did_this_help": [
                self.from_intent(value="yes", intent="intent_yes"),
                self.from_intent(value="no", intent="intent_no"),
            ]
        }

    async def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Once we have presented everything, we 'submit' the form"""

        found_result = tracker.get_slot("pest_summary_and_did_this_help")
        return [SlotSet("found_result", found_result)]

    @staticmethod
    def pest_summary(i, tracker: Tracker) -> str:
        """Prepare the text to show to user
        Returns None if there is nothing to show
        """

        text = None

        pests_summaries = tracker.get_slot("pests_summaries")
        if pests_summaries:
            hit_summary = pests_summaries[i]
            if hit_summary:
                if tracker.get_slot("bot_config_debug") or hit_summary[
                    "_score_weighted"
                ] >= tracker.get_slot("bot_config_score_threshold"):
                    text = f"{hit_summary['message']}"

        return text


class ActionConfigureBot(Action):
    """Configure the bot by setting the bot_config_----  slots.
    
    If a slot is already defined, we leave it as is.
    Else, we set it using the default value.
    """

    def name(self) -> Text:
        return "action_configure_bot"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:

        events = []
        for key in [
            "bot_config_debug",
            "bot_config_score_threshold",
            "bot_config_botname",
            "bot_config_urlprivacy",
        ]:
            value = tracker.get_slot(key)

            if value:
                # Correct the type in the tracker
                if key in ["bot_config_debug"]:
                    try:
                        value = bool(strtobool(str(value)))
                    except ValueError:
                        value = False
                if key in [
                    "bot_config_score_threshold",
                ]:
                    value = float(value)
            else:
                # If not yet configured, set default
                value = getattr(ac, key)

            events.append(SlotSet(key=key, value=value))

        active_form_name = None
        if tracker.active_form:
            active_form_name = tracker.active_form.get("name")

        if active_form_name:
            # list new bot configuration, revert tracker & next step is form
            events.extend([UserUtteranceReverted(), FollowupAction(active_form_name)])

        return events


class ActionListBotConfiguration(Action):
    """List the bot configuration"""

    def name(self) -> Text:
        return "action_list_bot_configuration"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        dispatcher.utter_message(text=summarize_bot_configuration(tracker))
        return []


def summarize_bot_configuration(tracker) -> str:
    """Prepares a message with the bot configurations in the slots"""
    bot_config_debug = tracker.get_slot("bot_config_debug")
    if bot_config_debug:
        keys = [
            "bot_config_debug",
            "bot_config_score_threshold",
            "bot_config_botname",
            "bot_config_urlprivacy",
        ]

        message = "\nNotes for tester:\n"
        for key in keys:
            message = message + f"- {key} = {tracker.get_slot(key)}\n"

        mydict = {}
        for key in keys:
            mydict[key] = str(tracker.get_slot(key))

        message = message + "\nOverwrite with:\n"
        for key in keys:
            message = (
                message
                + "/intent_configure_bot"
                + json.dumps({key: str(tracker.get_slot(key))})
                + "\n"
            )
    else:
        message = "To debug:\n"
        message = (
            message
            + "/intent_configure_bot"
            + json.dumps({"bot_config_debug": "True"})
            + "\n"
        )

    return message


def reset_slots_from_previous_forms():
    """Clean up slots from all previous forms"""
    events = []
    events.append(SlotSet("cause_damage_question", None))
    events.append(SlotSet("found_result", None))
    events.append(SlotSet("pest_causes_damage", None))
    events.append(SlotSet("pest_damage_description", None))
    events.append(SlotSet("pest_name", None))
    events.append(SlotSet("pest_problem_description", None))
    events.append(SlotSet("question", None))

    events.append(SlotSet("rating_value", None))

    events.append(SlotSet("pests_summaries", None))
    events.append(SlotSet("pests_summaries_index", None))
    events.append(SlotSet("pest_summary", None))
    events.append(SlotSet("pest_summary_and_did_this_help", None))

    events.append(SlotSet("said_hi", True))
    events.append(SlotSet("shown_privacypolicy", True))

    return events
