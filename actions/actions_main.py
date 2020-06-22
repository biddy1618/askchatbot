"""Custom Actions & Forms"""

import logging
import pprint
from typing import Any, Text, Dict, List, Union

from rasa_sdk import Action, Tracker
from rasa_sdk.forms import FormAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    SessionStarted,
    Restarted,
    FollowupAction,
    ActionExecuted,
    EventType,
    UserUttered,
)

import requests
import aiohttp

from actions import actions_config as ac


logger = logging.getLogger(__name__)

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


async def handle_es_query(query, index_name):
    """Handles an elastic search query"""

    if index_name != "ipmdata":
        raise Exception(f"Not implemented for index_name = {index_name}")

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
        print_summary=False,
    )

    pn_description_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "descriptionPestNote_vector",
        nested=False,
        best_image="first",
        print_summary=False,
    )

    pn_life_cycle_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "life_cycle_vector",
        nested=False,
        best_image="first",
        print_summary=False,
    )

    qt_content_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "contentQuickTips_vector",
        nested=False,
        best_image="first",
        print_summary=False,
    )

    pn_caption_hits = cosine_similarity_query(
        index_name,
        _source_query,
        query_vector,
        "imagePestNote.caption_vector",
        nested=True,
        best_image="caption",
        print_summary=False,
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

    # print_hits(hits, title="Combined & sorted hits")

    return hits


class ActionHi(Action):
    """Get the conversation going"""

    def name(self) -> Text:
        return "action_hi"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        shown_privacypolicy = tracker.get_slot("shown_privacypolicy")
        said_hi = tracker.get_slot("said_hi")
        explained_ipm = tracker.get_slot("explained_ipm")

        events = []

        if not said_hi:
            dispatcher.utter_message(template="utter_hi")
            dispatcher.utter_message(template="utter_summarize_skills")
            events.extend([SlotSet("said_hi", True)])

        if not shown_privacypolicy:
            dispatcher.utter_message(template="utter_inform_privacypolicy")
            events.extend([SlotSet("shown_privacypolicy", True)])

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

        return events


class ActionExplainIPM(Action):
    """Explain IPM"""

    def name(self) -> Text:
        return "action_explain_ipm"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        dispatcher.utter_message(template="utter_explain_ipm")
        return [SlotSet("explained_ipm", True)]


class FormQueryKnowledgeBase(FormAction):
    """Query the Knowledge Base"""

    def name(self) -> Text:
        return "form_query_knowledge_base"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""

        return ["pest_problem_description"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""

        return {
            "pest_problem_description": [self.from_text()],
        }

    async def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""

        pest_problem_description = tracker.get_slot("pest_problem_description")

        if ac.do_the_queries:
            hits = await handle_es_query(
                pest_problem_description, ac.ipmdata_index_name
            )

            # List only the top 3
            for hit in hits[:3]:
                name = hit["_source"]["name"]
                score = hit["_score"]
                pn_url = hit["_source"]["urlPestNote"]
                pn_image = None
                if hit["best_image"]:
                    pn_image = hit["best_image"]["src"]
                    pn_image_caption = hit["best_image"]["caption"]

                text = ""

                if pn_image:
                    text = f"{pn_image_caption}\n"

                if pn_url:
                    text = f"{text}- [pestnote for '{name}']({pn_url})\n"
                else:
                    text = f"{text}- {name}\n"

                text = f"{text}- similarity score={score:.1f}"

                dispatcher.utter_message(text=text, image=pn_image)

        else:
            message = (
                f"Not doing an actual elastic search query.\n"
                f"A query with the following details would be done: \n"
                f"pest problem description = "
                f"{pest_problem_description}"
            )
            dispatcher.utter_message(message)

        # return [AllSlotsReset()]
        return []


async def tag_convo(tracker: Tracker, label: Text) -> None:
    """Tag a conversation in Rasa X with a given label"""
    endpoint = f"http://{ac.rasa_x_host}/api/conversations/{tracker.sender_id}/tags"
    if not USE_AIOHTTP:
        try:
            response = requests.post(url=endpoint, data=label)
            logger.debug("Response status code: %s", response.status_code)
        except requests.exceptions.ConnectionError as e:
            logger.error("Rasa X connection error: %s", e)
    else:
        logger.info("using aiohttp module")
        # https://docs.aiohttp.org/en/stable/client_quickstart.html#make-a-request
        async with aiohttp.ClientSession() as session:
            async with session.post(url=endpoint, data=label) as response:
                logger.debug("Response status code %s", response.status)


class ActionTagRating(Action):
    """Tag rating of the conversation in Rasa X"""

    def name(self):
        return "action_tag_rating"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:

        rating_string = tracker.get_slot("rating_value")

        if rating_string not in ["1", "2", "3", "4", "5"]:
            logger.debug("Wrong rating %s. Will not tag in Rasa X", rating_string)
            return []

        rating = int(rating_string)
        # https://www.color-hex.com/color-palette/30630
        colors = ["ff4545", "ffa534", "ffe234", "b7dd29", "57e32c"]
        # Example for label:
        # '[{"value":"rating=2","color":"ffa534"}]'
        label = (
            '[{"value":"rating='
            + f"{rating}"
            + '","color":"'
            + f"{colors[rating-1]}"
            + '"}]'
        )
        await tag_convo(tracker, label)

        # return []
        # Start a new session by sending the session_start intent
        return next_intent_events("session_start_custom")


class ActionSessionStart(Action):
    """Greet the user right away when a session starts, not waiting until the
    user says something first."""

    def name(self) -> Text:
        """Overwrite the default action_session_start"""
        return "action_session_start_custom"

    @staticmethod
    def fetch_slots(tracker: Tracker) -> List[EventType]:
        """Collect the slots you want to carry over to the next session."""

        slots = []

        for key in ["shown_privacypolicy", "said_hi", "explained_ipm"]:
            value = tracker.get_slot(key)
            if value is not None:
                slots.append(SlotSet(key=key, value=value))

        logger.debug("Fetched slots = %s", pprint.pformat(slots))
        return slots

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        # the session should begin with a `session_started` event
        events = [SessionStarted()]

        # any slots that should be carried over should come after the
        # `session_started` event
        events.extend(self.fetch_slots(tracker))

        # pretend user also said 'hi'
        events.extend(next_intent_events("intent_hi"))

        return events


class ActionRestart(Action):
    """Restart the session"""

    def name(self) -> Text:
        return "action_restart"

    async def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        return [Restarted(), FollowupAction("action_session_start_custom")]
