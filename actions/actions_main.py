"""Custom Actions & Forms"""

import logging
import pprint
from typing import Any, Text, Dict, List, Union

from rasa_sdk import Action, Tracker
from rasa_sdk.forms import FormAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType, AllSlotsReset

import requests

from actions import actions_config as ac


logger = logging.getLogger(__name__)

USE_AIOHTTP = False


async def handle_es_query(query, index_name):
    """Handles an elastic search query"""

    # create the embedding vector
    query_vector = ac.embed([query]).numpy()[0]

    if index_name == "posts":
        cos = "cosineSimilarity(params.query_vector, doc['title_vector']) + 1.0"
        _source_query = {"includes": ["title", "body"]}
    elif index_name == "pestnotes":
        cos = "cosineSimilarity(params.query_vector, doc['description_vector']) + 1.0"
        _source_query = {
            "includes": ["name", "url", "description", "damage", "management", "images"]
        }
    else:
        raise Exception(f"Not implemented for index_name = {index_name}")

    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {"source": cos, "params": {"query_vector": query_vector},},
        }
    }

    # TODO: Use async elasticsearch client
    response = ac.es_client.search(
        index=index_name,
        body={"size": ac.search_size, "query": script_query, "_source": _source_query,},
    )

    return response


class ActionHi(Action):
    """Say Hi and show the privacy policy if not yet done"""

    def name(self) -> Text:
        return "action_hi"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        shown_privacypolicy = tracker.get_slot("shown_privacypolicy")
        if shown_privacypolicy:
            dispatcher.utter_message(template="utter_hi")
            return []

        dispatcher.utter_message(template="utter_hi")
        dispatcher.utter_message(template="utter_inform_privacypolicy")
        dispatcher.utter_message(template="utter_summarize_skills")
        return [SlotSet("shown_privacypolicy", True)]


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
            response = await handle_es_query(
                pest_problem_description, ac.pestnotes_index_name
            )

            if response["hits"]["hits"]:
                dispatcher.utter_message(text="I found some relevant pestnotes:")
            for hit in response["hits"]["hits"]:
                name = hit["_source"]["name"]
                score = hit["_score"]
                url = hit["_source"]["url"]
                image = None
                if hit["_source"]["images"]:
                    image = hit["_source"]["images"][0]["src"]

                text = f"{name} (score={score:.1f})"
                dispatcher.utter_message(text=text, url=url, image=image)

        else:
            message = (
                f"Not doing an actual elastic search query.\n"
                f"A query with the following details would be done: \n"
                f"pest problem description = "
                f"{pest_problem_description}"
            )
            dispatcher.utter_message(message)

        return [AllSlotsReset()]


class FormQueryStackOverflowIndex(FormAction):
    """Query the StackOverflow Index"""

    def name(self) -> Text:
        return "form_query_stackoverflow_in_es"

    @staticmethod
    def required_slots(tracker: Tracker) -> List[Text]:
        """A list of required slots that the form has to fill"""

        return ["stackoverflow_query"]

    def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
        """A dictionary to map required slots to
            - an extracted entity
            - intent: value pairs
            - a whole message
            or a list of them, where a first match will be picked"""

        return {
            "stackoverflow_query": [self.from_text()],
        }

    async def submit(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict]:
        """Define what the form has to do
            after all required slots are filled"""

        stackoverflow_query = tracker.get_slot("stackoverflow_query")

        if ac.do_the_queries:
            response = await handle_es_query(
                stackoverflow_query, ac.stackoverflow_index_name
            )
            hits = response["hits"]["hits"]
            if len(hits) == 0:
                message = "No Stackoverflow hits were found"
            else:
                message = (
                    f"Listing the Stackoverflow hits with highest score "
                    f"(max {ac.search_size}):\n"
                    f"{pprint.pformat(hits)}"
                )
        else:
            message = (
                f"Not doing an actual elastic search query.\n"
                f"A query with the following details would be done: \n"
                f"stackoverflow_query = "
                f"{stackoverflow_query}"
            )

        dispatcher.utter_message(message)
        return [AllSlotsReset()]


async def tag_convo(tracker: Tracker, label: Text) -> None:
    """Tag a conversation in Rasa X with a given label"""
    endpoint = f"http://{ac.rasa_x_host}/api/conversations/{tracker.sender_id}/tags"
    if not USE_AIOHTTP:
        response = requests.post(url=endpoint, data=label)
        logger.debug("Response status code: %s", response.status_code)
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

        return []
