"""Custom Actions & Forms"""

import os
import logging
import pprint
from typing import Any, Text, Dict, List, Union

from rasa_sdk import Action, Tracker
from rasa_sdk.forms import FormAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType, AllSlotsReset
import ruamel.yaml
import tensorflow_hub as tf_hub
from elasticsearch import Elasticsearch


logger = logging.getLogger(__name__)

# get configuration
es_config = ruamel.yaml.safe_load(open("credentials_elasticsearch.yml", "r")) or {}
stubquery = es_config.get("stubquery", True)
stackoverflow_index_name = es_config.get("stackoverflow-index-name")
tfhub_embedding_url = es_config.get("tfhub-embedding-url")

# define where the tfhub modules are stored
os.environ["TFHUB_CACHE_DIR"] = es_config.get("tfhub-cache-dir")

if stubquery:
    logger.info("Will skip elastic search queries (stubquery=%s)", stubquery)
else:
    logger.info("Will do elastic search queries (stubquery=%s)", stubquery)

logger.info("Start loading embedding module %s", tfhub_embedding_url)
embed = tf_hub.load(tfhub_embedding_url)
logger.info("Done loading embedding module %s", tfhub_embedding_url)


# initialize the elastic search client
es_client = Elasticsearch()
SEARCH_SIZE = 5


def handle_es_query(query, index_name):
    """Handles an elastic search query"""

    # create the embedding vector
    query_vector = embed([query]).numpy()[0]

    cos = "cosineSimilarity(params.query_vector, doc['title_vector']) + 1.0"
    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {"source": cos, "params": {"query_vector": query_vector},},
        }
    }

    response = es_client.search(
        index=index_name,
        body={
            "size": SEARCH_SIZE,
            "query": script_query,
            "_source": {"includes": ["title", "body"]},
        },
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
        dispatcher.utter_message(template="utter_what_is_chatgoal")
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
            "pest_problem_description": [self.from_text(intent=["intent_question"])],
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

        if stubquery:
            message = (
                f"Not doing an actual elastic search query.\n"
                f"A query with the following details would be done: \n"
                f"pest problem description = "
                f"{pest_problem_description}"
            )
        else:
            message = "TO-BE-IMPLEMENTED: QUERY TO KNOWLEDGE BASE"
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
            "stackoverflow_query": [self.from_text(intent=["intent_question"])],
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

        if stubquery:
            message = (
                f"Not doing an actual elastic search query.\n"
                f"A query with the following details would be done: \n"
                f"stackoverflow_query = "
                f"{stackoverflow_query}"
            )
        else:
            response = handle_es_query(stackoverflow_query, stackoverflow_index_name)
            hits = response["hits"]["hits"]
            if len(hits) == 0:
                message = "No Stackoverflow hits were found"
            else:
                message = (
                    f"Listing the Stackoverflow hits with highest score "
                    f"(max {SEARCH_SIZE}):\n"
                    f"{pprint.pformat(hits)}"
                )

        dispatcher.utter_message(message)
        return [AllSlotsReset()]
