"""Custom Actions & Forms"""
import logging
from pathlib import Path
from typing import Text, List

from rasa_sdk import Action, Tracker
from rasa_sdk.forms import FormAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    ActionExecuted,
    EventType,
    UserUttered,
)

from actions import actions_config as ac
from actions.actions_parquet import read_df

logger = logging.getLogger(__name__)

df = read_df(local_dir=f"{Path(__file__).parents[0]}", fname=ac.askextension_parquet)


class ActionRetrieval(Action):
    """Custom Retrieval Action for data coming out of the ResponseSelector (NLU)"""

    def name(self) -> Text:
        return "action_retrieval"

    async def run(self, dispatcher, tracker, domain) -> List[EventType]:
        event = tracker.events[-1]
        rankings = event["parse_data"]["response_selector"]["askextension_tomato"][
            "ranking"
        ]
        ostickets_california = []
        ostickets_other = []
        for rank in rankings:
            (_intent_a, intent_b) = rank["full_retrieval_intent"].split("/")
            (faq_id, state) = intent_b.split("_")
            faq_id = int(faq_id)
            osticket = {
                "url": f"{ac.askextension_url}/faq.php?id={faq_id}",
                "state": state,
                "confidence": rank["confidence"],
                "your-question": event["text"],
                "osticket-question": df.loc[faq_id, "question"],
                "osticket-answer": df.loc[faq_id, "answer"]["1"]["response"],
            }
            if state.lower() == "california":
                if len(ostickets_california) < 3:
                    ostickets_california.append(osticket)
            elif len(ostickets_other) < 3:
                ostickets_other.append(osticket)

            if len(ostickets_california) == 3 and len(ostickets_other) == 3:
                break

        if len(ostickets_california) > 0:
            message = "I found something of relevance from California:"
            dispatcher.utter_message(message)

            for osticket in ostickets_california:
                message = create_osticket_message(osticket)
                dispatcher.utter_message(message)

        if len(ostickets_other) > 0:
            message = "I found something of relevance from outside California:"
            dispatcher.utter_message(message)

            for osticket in ostickets_other:
                message = create_osticket_message(osticket)
                dispatcher.utter_message(message)

        return []


def create_osticket_message(osticket):
    """Create message to utter"""
    message = f"[osticket]({osticket['url']})\n"
    message = f"{message}- confidence: {osticket['confidence']:.2f}\n"
    message = f"{message}- state: {osticket['state']}\n"
    message = f"{message}- osticket answer: {osticket['osticket-answer']}\n"
    message = f"{message}- your question: {osticket['your-question']}\n"
    message = f"{message}- osticket question: {osticket['osticket-question']}\n"
    return message
