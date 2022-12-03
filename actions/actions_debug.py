'''
Module for debug actions.

Author: Dauren Baitursyn
'''
from typing import Dict, Text, Any, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (EventType, SlotSet)


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
        parameter, value, m = helper._parse_config_message(message)
        return_vals = []
        if message and parameter and parameter in config.config_keys: 
            setattr(config, parameter, value)
            return_vals = [SlotSet(parameter, value)]
            logger.info(f'action_set_parameter - setting parameter {parameter} to {value}')
            msg = f"Parameter <strong>{parameter}</strong> set to <strong>{value}</strong><br>"
            
        else: 
            dispatcher.utter_message(text    = "Error. Could not find parameter. Please refer to the current parameters and use the exact names")
            msg = 'Current parameters:<br><br>'
            for param in config.config_keys:
                msg += f'<strong>{param}</strong> = <i>{getattr(config, param)}</i><br>'
                
        dispatcher.utter_message(text=msg)
        logger.info(f'action_set_parameter - parameter parsing error - {None}')

        logger.info('action_set_parameter - END')

        return return_vals
    
class ActionShowParameters(Action):
    '''Action for setting client for testing purposes.'''

    def name(self) -> Text:
        return 'action_show_parameters'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:

        logger.info('action_show_parameters - START')
        msg = 'Current parameters:<br><br>'
        for param in config.config_keys:
            msg += f'<strong>{param}</strong> = <i>{getattr(config, param)}</i><br>'
        msg += f'<strong>stage</strong> = <i>{getattr(config, "stage")}</i><br>'
        dispatcher.utter_message(text=msg)
        logger.info('action_show_parameters - END')
        return []