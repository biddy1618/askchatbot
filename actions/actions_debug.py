from typing import Dict, Text, Any, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    SlotSet,
    FollowupAction,
    EventType
)

import logging
logger = logging.getLogger(__name__)

from actions.es import config
from actions import helper

class ActionSetParameter(Action):
    '''Action for setting parameter for debugging purposes.'''

    def name(self) -> Text:
        return 'action_set_parameter'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:

        logger.info('action_set_parameter - START')

        message = tracker.latest_message.get('text', None)
        parameter, value = helper._parse_config_message(message)
        
        if parameter: 
            dispatcher.utter_message(text = f'Setting parameter {parameter} to {value}')
            setattr(config, parameter, value)
            
            logger.info(f'action_set_parameter - setting parameter {parameter} to {value}')

        else: 
            dispatcher.utter_message(
                text    = (
                    f'Error parsing config message: </br>'                      +
                    'Please, use explicit parameter names</br>'                 +
                    '(i.e. <strong>parameter es_cut_off 0.5</strong>).'         +
                    '</br>Available parameters: <i>'                            +
                    ', '.join(helper.params.keys())                                    +
                    '</i>.')
            )
            logger.info(f'action_set_parameter - parameter parsing error - {None}')
        
            

        logger.info('action_set_parameter - END')

        return []