"""Custom Actions & Forms"""

import logging
import json
from typing import Any, Text, Dict, List, Union

from rasa_sdk import Action, Tracker
from rasa_sdk.forms import FormAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    ActionExecuted,
    EventType,
    UserUttered,
)

##import requests
##import aiohttp
import inflect

from actions import actions_config as ac


logger = logging.getLogger(__name__)
inflecter = inflect.engine()

USE_AIOHTTP = False

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

    if print_summary and (best_image == "first" or best_video == "first"):
        # print it before filling out best_image & best_video fields
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
        raise Exception(f"Not implemented. best_video = {best_video}")

    if print_summary and (best_image == "caption" or best_video == "title"):
        # print it after filling out best_image or best_video fields
        print_hits(hits, title=vector_name)

    return hits


def set_first_image_as_best(hits):
    """When scored we do not know the best image. Just pick the first."""
    for i, hit in enumerate(hits):
        hits[i]["best_image"] = None
        if hit["_source"]["imagePestNote"]:
            hits[i]["best_image"] = hit["_source"]["imagePestNote"][0]
        elif hit["_source"]["imageQuickTips"]:
            hits[i]["best_image"] = hit["_source"]["imageQuickTips"][0]

    return hits


def set_first_video_as_best(hits):
    """When scored we do not know the best video. Just pick the first."""
    for i, hit in enumerate(hits):
        hits[i]["best_video"] = None
        if hit["_source"]["video"]:
            hits[i]["best_image"] = hit["_source"]["video"][0]

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
            f'image-caption={(hit.get("best_image", {}) or {}).get("caption")}; '
            f'video-title={(hit.get("best_video", {}) or {}).get("videoTitle")}'
        )


async def handle_es_query(
    pest_problem_description,
    pest_damage_description,
    index_name,
    weight_description,
    weight_damage,
    print_summary=False,
):
    """Handles an elastic search query"""

    if index_name not in ["ipmdata", "ipmdata-dev"]:
        raise Exception(f"Not implemented for index_name = {index_name}")

    # create the embedding vectors
    query_vector = ac.embed([pest_problem_description]).numpy()[0]

    damage_vector = None
    if pest_damage_description:
        damage_vector = ac.embed([pest_damage_description]).numpy()[0]

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
        best_video="first",
        print_summary=print_summary,
    )

    pn_description_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "descriptionPestNote_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    pn_life_cycle_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "life_cycle_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    qt_content_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "contentQuickTips_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    pn_caption_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "imagePestNote.caption_vector",
        nested=True,
        best_image="caption",
        best_video="first",
        print_summary=print_summary,
    )

    qt_caption_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "imageQuickTips.caption_vector",
        nested=True,
        best_image="caption",
        best_video="first",
        print_summary=print_summary,
    )

    video_link_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "video.videoTitle_vector",
        nested=True,
        best_image="first",
        best_video="title",
        print_summary=print_summary,
    )

    pn_damage_hits = []
    if pest_damage_description:
        pn_damage_hits = cosine_similarity_query(
            index_name,
            _source_query,
            damage_vector,
            "damagePestNote_vector",
            nested=False,
            best_image="first",
            best_video="first",
            print_summary=print_summary,
        )

    ##########################################
    # Combine all hits and sort to max score #
    ##########################################

    # Scores based on description vector
    hits = pn_name_hits
    for hit2 in (
        pn_description_hits
        + pn_life_cycle_hits
        + qt_content_hits
        + pn_caption_hits
        + qt_caption_hits
        + video_link_hits
    ):
        duplicate = False
        for i, hit in enumerate(hits):
            if hit2["_source"]["name"] == hit["_source"]["name"]:
                hits[i]["_score"] = max(hit["_score"], hit2["_score"])
                hits[i]["best_image"] = hit2["best_image"]
                hits[i]["best_video"] = hit2["best_video"]
                duplicate = True
                break
        if not duplicate:
            hits.append(hit2)

    hits = sorted(hits, key=lambda h: h["_score"], reverse=True)

    if print_summary:
        print_hits(hits, title="Combined & sorted hits")

    # Scores based on damage vector
    if len(hits) > 0:
        for i, hit in enumerate(hits):
            hits[i]["_score_damage"] = 0.0
        if pest_damage_description:
            for i, hit in enumerate(hits):
                for hit_damage in pn_damage_hits:
                    if hit_damage["_source"]["name"] == hit["_source"]["name"]:
                        hits[i]["_score_damage"] = hit_damage["_score"]
                        break

    # Apply weighting
    for i, hit in enumerate(hits):
        hits[i]["_score_weighted"] = (
            weight_description * hits[i]["_score"]
            + weight_damage * hits[i]["_score_damage"]
        )

    # Sort to weighted score
    hits = sorted(hits, key=lambda h: h["_score_weighted"], reverse=True)

    # Do not filter on threshold. Leave this up to the caller
    return hits


class ActionHi(Action):
    """Get the conversation going"""

    def name(self) -> Text:
        return "action_hi"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        events = []

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
            {
                "title": "I have a pest",
                "payload": '/intent_chatgoal{"chatgoal_value":"I_have_a_pest"}',
            }
        )

        if not explained_ipm:
            buttons.append(
                {
                    "title": "Explain IPM",
                    "payload": '/intent_chatgoal{"chatgoal_value":"explain_ipm"}',
                }
            )

        if said_hi:
            buttons.append(
                {"title": "Goodbye", "payload": "/intent_bye",}
            )
        dispatcher.utter_message(
            text="Please select one of these options", buttons=buttons
        )

        # Make sure to clean up slots from all previous forms
        events.append(SlotSet("cause_damage_question", None))
        events.append(SlotSet("chatgoal_value", None))
        events.append(SlotSet("found_result", None))
        events.append(SlotSet("pest_causes_damage", None))
        events.append(SlotSet("pest_damage_description", None))
        events.append(SlotSet("pest_name", None))
        events.append(SlotSet("pest_problem_description", None))
        events.append(SlotSet("rating_value", None))
        events.append(SlotSet("said_hi", True))
        events.append(SlotSet("shown_privacypolicy", True))

        return events


class ActionExplainIPM(Action):
    """Explain IPM"""

    def name(self) -> Text:
        return "action_explain_ipm"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        dispatcher.utter_message(template="utter_explain_ipm")
        return [SlotSet("explained_ipm", True)]


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

        slots = ["pest_problem_description"]

        if tracker.get_slot("pest_causes_damage") != "no":
            slots.extend(
                ["pest_causes_damage", "pest_damage_description",]
            )

        return slots

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""

        return {
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

    async def validate_pest_problem_description(
        self,
        value: Text,
        _dispatcher: CollectingDispatcher,
        tracker: Tracker,
        _domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Once pest problem is described, build damage question to ask, using the
        pest name in plural form, if it was extracted from the pest problem 
        description"""

        pest_name = tracker.get_slot("pest_name")
        if not pest_name:
            question = "Is it causing any damage?"
        else:
            pest_plural = self.pest_name_plural(pest_name)
            question = f"Are the {pest_plural} causing any damage?"

        return {"pest_problem_description": value, "cause_damage_question": question}

    async def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""

        pest_problem_description = tracker.get_slot("pest_problem_description")
        pest_causes_damage = tracker.get_slot("pest_causes_damage")
        pest_damage_description = None
        if pest_causes_damage == "yes":
            pest_damage_description = tracker.get_slot("pest_damage_description")

        if ac.do_the_queries:
            hits = await handle_es_query(
                pest_problem_description,
                pest_damage_description,
                ac.ipmdata_index_name,
                float(tracker.get_slot("bot_config_weight_description")),
                float(tracker.get_slot("bot_config_weight_damage")),
                print_summary=False,
            )

            # Filter to threshold
            hits_filtered = [
                hit
                for hit in hits
                if (
                    hit["_score_weighted"]
                    >= float(tracker.get_slot("bot_config_score_threshold"))
                )
            ]

            if len(hits_filtered) == 0:
                text = (
                    "Notes for tester:\n"
                    "I did not find anything within the scoring threshold\n"
                    "The closest match is: \n"
                )
                text = text + create_text_for_pest(hits[0], tracker)
                dispatcher.utter_message(text=text)

                return [SlotSet("found_result", "no")]

            # List only the top 3
            text = (
                "I think I found something that could help you. "
                "Please click the links below for more details:"
            )
            dispatcher.utter_message(text=text)

            for hit in hits_filtered[:3]:
                dispatcher.utter_message(text=create_text_for_pest(hit, tracker))
                # dispatcher.utter_message(text=text, image=pn_image)

            return [SlotSet("found_result", "yes")]

        message = (
            f"Not doing an actual elastic search query.\n"
            f"A query with the following details would be done: \n"
            f"pest problem description = "
            f"{pest_problem_description}\n"
            f"pest damage description = "
            f"{pest_damage_description}"
        )
        dispatcher.utter_message(message)
        return [SlotSet("found_result", "yes")]


class ActionConfigureBot(Action):
    """Configure the bot by setting the bot_config_----  slots.
    
    If a slot is already defined, we leave it as is.
    Else, we set it using the default value.
    """

    def name(self) -> Text:
        return "action_configure_bot"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:

        # if not yet configured, set default bot configurations
        events = []
        for key in [
            "bot_config_weight_description",
            "bot_config_weight_damage",
            "bot_config_score_threshold",
            "bot_config_botname",
            "bot_config_urlprivacy",
        ]:
            value = tracker.get_slot(key)
            value_default = getattr(ac, key)
            if value is None:
                events.append(SlotSet(key=key, value=value_default))

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
    keys = [
        "bot_config_weight_description",
        "bot_config_weight_damage",
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

    return message


def create_text_for_pest(hit, tracker) -> str:
    """Prepares a message for the user"""
    name = hit["_source"]["name"]
    score_weighted = hit["_score_weighted"]
    score = hit["_score"]
    score_damage = hit["_score_damage"]
    pn_url = hit["_source"]["urlPestNote"]
    qt_url = hit["_source"]["urlQuickTip"]
    # pn_image = None
    # if hit["best_image"]:
    #    pn_image = hit["best_image"]["src"]
    #    pn_image_caption = hit["best_image"]["caption"]

    # if pn_image:
    #    text = f"{name}: {pn_image_caption}\n"
    # else:
    #    text = f"{name}\n"
    text = f"{name}\n"

    if qt_url:
        text = f"{text}- [quick tips]({qt_url})\n"
    if pn_url:
        text = f"{text}- [pestnote]({pn_url})\n"

    if hit["best_video"]:
        video_title = hit["best_video"]["videoTitle"]
        video_link = hit["best_video"]["videoLink"]
        text = f"{text}- [video: '{video_title}']({video_link})\n\n"

    text = f"{text}Notes for tester:\n"
    text = f"{text}- weighted similarity score = {score_weighted:.1f}\n"
    text = f"{text}- score for description = {score:.1f}\n"
    text = f"{text}- score for damage = {score_damage:.1f}\n"
    text = (
        f"{text}- weight for description = "
        f"{float(tracker.get_slot('bot_config_weight_description')):.2f}\n"
    )
    text = (
        f"{text}- weight for damage = "
        f"{float(tracker.get_slot('bot_config_weight_damage')):.2f}\n"
    )
    text = (
        f"{text}- score threshold = "
        f"{float(tracker.get_slot('bot_config_score_threshold')):.2f}\n"
    )
    return text
