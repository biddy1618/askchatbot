"""Custom Actions & Forms"""

import logging
from typing import Any, Text, Dict, List, Union

from rasa_sdk import Action, Tracker
from rasa_sdk.forms import FormAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType, AllSlotsReset
import ruamel.yaml

logger = logging.getLogger(__name__)

#
# get knowledge base configuration
#
kb_config = ruamel.yaml.safe_load(open("credentials_knowledge_base.yml", "r")) or {}
# TODO: is there a username & password ?
kb_user = kb_config.get("kb_user")
kb_pw = kb_config.get("kb_pw")
kb_instance = kb_config.get("kb_instance")
localmode = kb_config.get("localmode", True)
logger.debug("Local mode: %i", localmode)

base_api_url = f"https://{kb_instance}/api"


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
            "pest_problem_description": [
                self.from_text(intent=["intent_pest_problem_description"])
            ],
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

        if localmode:
            message = (
                f"Running in local mode.\n"
                f"An query with the following details would be done "
                f"if the knowledge base was connected:\n"
                f"pest problem description = "
                f"{pest_problem_description}"
            )
        else:
            message = "TO-BE-IMPLEMENTED: QUERY TO KNOWLEDGE BASE"
        dispatcher.utter_message(message)
        return [AllSlotsReset()]
