# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


from typing import Dict, Text, Any, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import (
    SlotSet,
    FollowupAction,
    EventType
)

import logging
logger = logging.getLogger(__name__)

from actions import helper


class ActionGreet(Action):
    '''Get the conversation going.'''

    def name(self) -> Text:
        return 'action_greet'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:
        
        logger.info('action_greet - START')
        shown_greeting          = tracker.get_slot('shown_greeting')
        shown_explain_ipm       = tracker.get_slot('shown_explain_ipm')
        
        done_query              = tracker.get_slot('done_query')

        if not shown_greeting:
            dispatcher.utter_message(response = 'utter_greet')
        
        buttons = [
            {'title': 'I would like to ask question.'       , 'payload': '/intent_help_question'},
        ]

        if not shown_explain_ipm:
            buttons.append({'title': 'I want to learn more about IPM'       , 'payload': '/intent_explain_ipm'      })

        if done_query:
            buttons.append({'title': 'Connect me to askextension expert.'   , 'payload': '/intent_request_expert'   })
        
        dispatcher.utter_message(text = 'How can I help you?', buttons = buttons)
        events = helper._reset_slots(tracker)

        logger.info('action_greet - END')
        return events



class ActionExplainIPM(Action):
    '''Explain IPM.'''

    def name(self) -> Text:
        return 'action_explain_ipm'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:

        logger.info('action_explain_ipm - START')
        
        dispatcher.utter_message(response = 'utter_explain_ipm')
        
        logger.info('action_explain_ipm - END')
        return [SlotSet('shown_explain_ipm', True), FollowupAction('action_greet')]
