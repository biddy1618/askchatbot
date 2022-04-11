from typing import Dict, Text, Any, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    EventType,
)

import logging
logger = logging.getLogger(__name__)

from actions import helper


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

        dispatcher.utter_message(text = helper.utterances['ipm'])
        
        logger.info('action_explain_ipm - END')
        return [SlotSet('shown_explain_ipm', True)]


class ActionConnectExpert(Action):
    '''Connect expert.'''

    def name(self) -> Text:
        return 'action_connect_expert'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:
        
        logger.info('action_connect_expert - START')
        buttons = [helper.buttons['start_over']]

        dispatcher.utter_message(text = helper.utterances['connect_expert'], buttons = buttons)
        logger.info('action_connect_expert - END')
        return []
