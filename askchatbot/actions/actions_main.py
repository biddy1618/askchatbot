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
            "urlPestDiseaseItems",
            "descriptionPestDiseaseItems",
            "identificationPestDiseaseItems",
            "life_cyclePestDiseaseItems",
            "damagePestDiseaseItems",
            "solutionsPestDiseaseItems",
            "urlTurfPests",
            "textTurfPests",
            "imagesTurfPests",
            "urlWeedItems",
            "descriptionWeedItems",
            "imagesWeedItems",
        ]
    }

    # ipmdata.json
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

    # cleanedPestDiseaseItems.json
    pdi_description_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "descriptionPestDiseaseItems_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    pdi_identification_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "identificationPestDiseaseItems_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    pdi_life_cycle_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "life_cyclePestDiseaseItems_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    pdi_damage_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "damagePestDiseaseItems_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    pdi_solutions_hits = cosine_similarity_query(
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
    tp_text_hits = cosine_similarity_query(
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
    wi_description_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "descriptionWeedItems_vector",
        nested=False,
        best_image="first",
        best_video="first",
        print_summary=print_summary,
    )

    do_nested = False
    pn_caption_hits = []
    qt_caption_hits = []
    video_link_hits = []
    if not do_nested:
        print("SKIPPING SEARCH IN NESTED FIELDS")
    if do_nested:
        # ipmdata.json
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
        + pdi_description_hits
        + pdi_identification_hits
        + pdi_life_cycle_hits
        + pdi_damage_hits
        + pdi_solutions_hits
        + tp_text_hits
        + wi_description_hits
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
                for hit_damage in pdi_damage_hits:
                    if hit_damage["_source"]["name"] == hit["_source"]["name"]:
                        hits[i]["_score_damage"] = max(
                            hits[i]["_score_damage"], hit_damage["_score"]
                        )
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
            {"title": "I have a pest", "payload": "/intent_i_have_a_pest",}
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
                tracker.get_slot("bot_config_weight_description"),
                tracker.get_slot("bot_config_weight_damage"),
                print_summary=False,
            )
        else:
            message = (
                f"Not doing an actual elastic search query.\n"
                f"A query with the following details would be done: \n"
                f"pest problem description = "
                f"{pest_problem_description}\n"
                f"pest damage description = "
                f"{pest_damage_description}"
            )
            dispatcher.utter_message(message)
            hits = []

        pests_summaries = summarize_hits(hits, tracker)
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

        pests_summaries_index = 0
        pest_summary = self.pest_summary(pests_summaries_index, tracker)

        if pest_summary:
            return {
                "pests_summaries": value,
                "pests_summaries_index": pests_summaries_index,
                "pest_summary": pest_summary + "\nDid this help?",
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
        pests_summaries_index = tracker.get_slot("pests_summaries_index") + 1
        pest_summary = self.pest_summary(pests_summaries_index, tracker)

        if pest_summary:
            # we have more to present
            return {
                "pest_summary_and_did_this_help": None,
                "pests_summaries_index": pests_summaries_index,
                "pest_summary": pest_summary + "\nDid this help?",
            }

        # we have nothing more to present
        return {"pest_summary_and_did_this_help": value}

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
        pests_summaries = tracker.get_slot("pests_summaries")

        found_result = "no"

        hit_summary = None
        if pests_summaries:
            hit_summary = pests_summaries[i]
            if hit_summary["_score_weighted"] >= tracker.get_slot(
                "bot_config_score_threshold"
            ):
                found_result = "yes"

        text = None

        header = None
        if i == 0:
            if found_result == "yes":
                header = (
                    "I think I found something that could help you. "
                    "Please click the links below for more details:"
                )
            elif tracker.get_slot("bot_config_debug"):
                if hit_summary:
                    header = (
                        "Notes for tester:\n"
                        "I did not find anything within the scoring threshold\n"
                        "The closest match is: \n"
                    )
                    found_result = "yes"

        elif i == 1:
            if found_result == "yes":
                header = "Ok, what about this:"
        elif i == 2:
            if found_result == "yes":
                header = "Mmmm..., I have one more that I think is useful:"
        else:
            # Note, we should never get here, but make it robust against that
            if found_result == "yes":
                header = "What about this:"

        text = header

        if found_result == "yes":
            text = f"{text}\n {hit_summary['message']}"
            # dispatcher.utter_message(text=message, image=pn_image)

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
            "bot_config_weight_description",
            "bot_config_weight_damage",
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
                    "bot_config_weight_description",
                    "bot_config_weight_damage",
                    "bot_config_score_threshold",
                ]:
                    value = float(value)
            else:
                # If not yet configured, set default
                value = getattr(ac, key)

            events.append(SlotSet(key=key, value=value))

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
    else:
        message = "To debug:\n"
        message = (
            message
            + "/intent_configure_bot"
            + json.dumps({"bot_config_debug": "True"})
            + "\n"
        )

    return message


def summarize_hits(hits, tracker) -> list:
    """Create a list of dictionaries, where each dictionary contains those items we
    want to use when presenting the hits in a conversational manner to the user."""
    pests_summaries = []
    if not hits:
        return pests_summaries

    for hit in hits:
        hit_summary = {}

        hit_summary["_score_weighted"] = hit["_score_weighted"]
        hit_summary["message"] = create_text_for_pest(hit, tracker)

        pests_summaries.append(hit_summary)

    return pests_summaries


def reset_slots_from_previous_forms():
    """Clean up slots from all previous forms"""
    events = []
    events.append(SlotSet("cause_damage_question", None))
    events.append(SlotSet("found_result", None))
    events.append(SlotSet("pest_causes_damage", None))
    events.append(SlotSet("pest_damage_description", None))
    events.append(SlotSet("pest_name", None))
    events.append(SlotSet("pest_problem_description", None))

    events.append(SlotSet("rating_value", None))

    events.append(SlotSet("pests_summaries", None))
    events.append(SlotSet("pests_summaries_index", None))
    events.append(SlotSet("pest_summary", None))
    events.append(SlotSet("pest_summary_and_did_this_help", None))

    events.append(SlotSet("said_hi", True))
    events.append(SlotSet("shown_privacypolicy", True))

    return events


def create_text_for_pest(hit, tracker) -> str:
    """Prepares a message for the user"""
    name = hit["_source"]["name"]
    score_weighted = hit["_score_weighted"]
    score = hit["_score"]
    score_damage = hit["_score_damage"]
    pn_url = hit["_source"]["urlPestNote"]
    qt_url = hit["_source"]["urlQuickTip"]
    pdi_url = hit["_source"]["urlPestDiseaseItems"]
    tp_url = hit["_source"]["urlTurfPests"]
    wi_url = hit["_source"]["urlWeedItems"]
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
        text = f"{text}- [quick tip]({qt_url})\n"
    if pn_url:
        text = f"{text}- [pestnote]({pn_url})\n"
    if pdi_url:
        text = f"{text}- [pest disease item]({pdi_url})\n"
    if tp_url:
        text = f"{text}- [turf pest]({tp_url})\n"
    if wi_url:
        text = f"{text}- [weed item]({wi_url})\n"

    if hit["best_video"]:
        video_title = hit["best_video"]["videoTitle"]
        video_link = hit["best_video"]["videoLink"]
        text = f"{text}- [video: '{video_title}']({video_link})\n\n"

    if tracker.get_slot("bot_config_debug"):
        text = f"{text}\nNotes for tester:\n"
        text = f"{text}- weighted similarity score = {score_weighted:.1f}\n"
        text = f"{text}- score for description = {score:.1f}\n"
        text = f"{text}- score for damage = {score_damage:.1f}\n"
        text = (
            f"{text}- weight for description = "
            f"{tracker.get_slot('bot_config_weight_description'):.2f}\n"
        )
        text = (
            f"{text}- weight for damage = "
            f"{tracker.get_slot('bot_config_weight_damage'):.2f}\n"
        )
        text = (
            f"{text}- score threshold = "
            f"{tracker.get_slot('bot_config_score_threshold'):.2f}\n"
        )
    return text
