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
        shown_privacy_policy    = tracker.get_slot('shown_privacy_policy')
        shown_explain_ipm       = tracker.get_slot('shown_explain_ipm')

        if not shown_greeting:
            dispatcher.utter_message(response = 'utter_greet')
        
        if not shown_privacy_policy:
            dispatcher.utter_message(response = 'utter_privacy_policy')
        
        buttons = [
            {'title': 'I have problem with my plant.',                          'payload': '/request_plant_problem'},
            {'title': 'I have a picture and I would like to get help on that.', 'payload': '/request_plant_picture'},
            {'title': 'I have generic request.',                                'payload': '/request_generic'},
            {'title': 'Connect me to askextension expert.',                     'payload': '/request_expert'},
        ]

        if not shown_explain_ipm:
            buttons.append({'title': 'I want to learn more about IPM', 'payload': '/intent_explain_ipm'})

        if shown_greeting:
            buttons.append({'title': 'Goodbye', 'payload': '/intent_goodbye'})

        dispatcher.utter_message(text = 'Please, select one of the these options:', buttons = buttons)
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
