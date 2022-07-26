# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


from typing import Dict, Text, Any, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import (
    EventType,
    UserUtteranceReverted
)

from elasticsearch import RequestError

import logging
logger = logging.getLogger(__name__)

from actions import helper
from actions.es import config
from actions.es.es import save_chat_logs





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
            if config.debug: dispatcher.utter_message(text = helper._get_config_message(config))    
            dispatcher.utter_message(text = helper.utterances['greet'])
        
        buttons = [helper.buttons['ask_question']]

        if not shown_explain_ipm: buttons.append(helper.buttons['learn_ipm'     ])
        if done_query           : buttons.append(helper.buttons['request_expert'])
        
        dispatcher.utter_message(text = helper.utterances['help'], buttons = buttons)
        events = helper._reset_slots(tracker)
        logger.info('action_greet - END')
        return events


class ActionGoodbye(Action):
    '''Say good bye.'''

    def name(self) -> Text:
        return 'action_goodbye'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:

        logger.info('action_goodbye - START')
        buttons = [helper.buttons['start_over']]

        dispatcher.utter_message(text = helper.utterances['goodbye'], buttons = buttons)
        logger.info('action_goodbye - END')
        return []


class ActionIamBot(Action):
    '''Bot challenge.'''

    def name(self) -> Text:
        return 'action_iambot'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:

        logger.info('action_iambot - START')
        buttons = [helper.buttons['start_over']]

        dispatcher.utter_message(text = helper.utterances['iambot'], buttons = buttons)
        logger.info('action_iambot - END')
        return []


class ActionDefaultFallback(Action):
    '''Action for default fallback.'''

    def name(self) -> Text:
        return 'action_default_fallback'
    
    async def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:
        
        logger.info('action_default_fallback - START')
        buttons = [
            helper.buttons['start_over'     ],
            helper.buttons['request_expert' ]
        ]

        logger.info('action_default_fallback - saving chat history due to `UserUtteranceReverted` action - START')
        
        chat_history = helper._parse_tracker_events(tracker.events)
        
        export = {
            'chat_id'       : tracker.sender_id             ,
            'timestamp'     : chat_history[0]['timestamp']  ,
            'chat_history'  : chat_history
        }

        try:
            await save_chat_logs(export)
        except RequestError as e:
            logger.error(f'action_default_fallback - error while indexing - failed to save conversation with chat_id - {export["chat_id"]}')
        except AssertionError as e:
            logger.error(f'action_default_fallback - error on ES side - failed to save conversation with chat_id - {export["chat_id"]}')     
        
        logger.info('action_default_fallback - saved chat history - END')
        

        dispatcher.utter_message(text = helper.utterances['fallback'], buttons = buttons)
        logger.info('action_default_fallback - END')
        return [UserUtteranceReverted()]


class ActionOutOfScope(Action):
    '''Action for default fallback.'''

    def name(self) -> Text:
        return 'action_out_of_scope'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:
        
        logger.info('action_out_of_scope - START')
        buttons = [
            helper.buttons['start_over'     ],
            helper.buttons['request_expert' ]
        ]

        dispatcher.utter_message(text = helper.utterances['out_of_scope'], buttons = buttons)
        logger.info('action_out_of_scope - END')
        return []