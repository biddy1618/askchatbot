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
    """Get the conversation going."""

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
    """Explain IPM"""

    def name(self) -> Text:
        return "action_explain_ipm"
    
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


class ActionAskForPlantType(Action):
    """Custom action for slot validation - plant_type"""
    
    def name(self) -> Text:
        return 'action_ask_plant_type'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:

        logger.info('action_ask_plant_type - START')
        
        buttons = [
            {'title': 'Flowers',        'payload': '/request_plant_problem{"plant_type": "flowers"}'},
            {'title': 'Fruits',         'payload': '/request_plant_problem{"plant_type": "fruits"}'},
            {'title': 'Vegetables',     'payload': '/request_plant_problem{"plant_type": "vegetables"}'},
            {'title': 'Trees',           'payload': '/request_plant_problem{"plant_type": "trees"}'},
            {'title': 'I don\'t know',  'payload': '/request_plant_problem{"plant_type": "other"}'}
        ]

        dispatcher.utter_message(text = 'Please, select your plant type:', buttons = buttons)

        logger.info('action_ask_plant_type - END')
        return []

class ActionAskForPlantName(Action):
    """Custom action for slot validation - plant_name"""
    
    def name(self) -> Text:
        return 'action_ask_plant_name'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:

        logger.info('action_ask_plant_name - START')

        plant_type = tracker.get_slot('plant_type')
        pn = helper._get_plant_names(plant_type = plant_type, n = 10)
        
        buttons = [{'title': name, 'payload': '/request_plant_problem{"plant_name": "' + name + '"}'} for name in pn]
        buttons.append({'title': 'other', 'payload': '/request_plant_problem{"plant_name": "other"}'})
        
        dispatcher.utter_message(text = 'Please, select or write the name of your plant:', buttons = buttons)

        logger.info('action_ask_plant_name - END')
        return []

class ActionAskForPlantPart(Action):
    """Custom action for slot validation - plant_part"""
    
    def name(self) -> Text:
        return 'action_ask_plant_part'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:

        logger.info('action_ask_plant_part - START')

        plant_type = tracker.get_slot('plant_type')
        plant_name = tracker.get_slot('plant_name')
        pp = helper._get_plant_parts(
            plant_type = plant_type, 
            plant_name = plant_name,
            n = 10)

        buttons = [{'title': part, 'payload': '/request_plant_problem{"plant_part": "' + part + '"}'} for part in pp]
        buttons.append({'title': 'other', 'payload': '/request_plant_problem{"plant_part": "other"}'})
        
        dispatcher.utter_message(text = 'Please, select your plant part:', buttons = buttons)

        logger.info('action_ask_plant_part - END')
        return []


class ActionAskForPlantDamage(Action):
    """Custom action for slot validation - plant_damages"""
    
    def name(self) -> Text:
        return 'action_ask_plant_damages'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:

        logger.info('action_ask_plant_damages - START')

        plant_type = tracker.get_slot('plant_type')
        plant_name = tracker.get_slot('plant_name')
        plant_part = tracker.get_slot('plant_part')
        
        pd = helper._get_plant_damages(
            plant_type = plant_type, 
            plant_name = plant_name,
            plant_part = plant_part,
            n = 10)
        buttons = [{'title': 'I don\'t have any description', 'payload': '/request_plant_problem{"plant_damage": ["other"]}'}]

        dispatcher.utter_message(text = 'Please, describe your damage using explicit descriptive words as below:')
        dispatcher.utter_message(text = ', '.join(pd), buttons = buttons)

        
        logger.info('action_ask_plant_damages - END')
        return []

class ValidatePlantProblemForm(FormValidationAction):
    """
    Form for plant problem description validation form.
    Required slots:
    - plant_type
    - plant_name
    - plant_part
    - plant_damage
    """


    def name(self) -> Text:
        return "validate_plant_problem_form"

    async def extract_plant_damages(
        self, dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[Text, Any]
    ) -> Dict[Text, Any]:
        """Custom slot extraction for plant_damages"""

        logger.info(f'Requested slot: {tracker.slots["requested_slot"]}')
            
        if tracker.slots['requested_slot'] != 'plant_damages':
            logger.info(f'REQUESTING SLOT: {tracker.slots["requested_slot"]}')
            return {}

        logger.info('validate_plant_problem_form - extract_plant_damages - START')
        
        last_message = tracker.latest_message.get("text")
        
        logger.info(f'validate_plant_problem_form - extract_plant_damages - last message {last_message}')
        plant_damages = last_message

        logger.info(f'validate_plant_problem_form - extract_plant_damages - extracted values {plant_damages}')
        return {"plant_damages": plant_damages}
    
    def validate_plant_type(
        self,
        value       : Text,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate slot plant_type"""

        logger.info('validate_plant_problem_form - validate_plant_type - START')
        logger.info(f'validate_plant_problem_form - validate_plant_type - SLOT VALUE: {value}')

        plant_type = None
        if value: plant_type = value
        else: dispatcher.utter_message(
            text = 'This kind of plant type is not recognized. '\
                'Press button "I don\'t know" if you don\'t know '\
                'the plant type.')
        
        logger.info('validate_plant_problem_form - validate_plant_type - END')
        return {'plant_type': plant_type}

    def validate_plant_name(
        self,
        value       : Text,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate slot plant_name"""
    
        logger.info('validate_plant_problem_form - validate_plant_name - START')
        logger.info(f'validate_plant_problem_form - validate_plant_name - SLOT VALUE: {value}')
        
        plant_name = None
        if value: plant_name = value
        else: dispatcher.utter_message(
            text = 'This kind of plant name is not recognized. '\
                'Press button "I don\'t know" if you don\'t know '\
                'the plant name.')
        
        logger.info('validate_plant_problem_form - validate_plant_name - END')
        return {'plant_name': plant_name}

    def validate_plant_part(
        self,
        value       : Text,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain  : Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate slot plant_part"""

        logger.info('validate_plant_problem_form - validate_plant_part - START')
        logger.info(f'validate_plant_problem_form - validate_plant_part - SLOT VALUE: {value}')
        
        plant_part = None
        if value:
            plant_part = value
        else: dispatcher.utter_message(
            text = 'This kind of plant part is not recognized. '\
                'Press button "I don\'t know" if you don\'t know '\
                'the plant part.')
            
        
        logger.info('validate_plant_problem_form - validate_plant_part - END')
        return {'plant_part': plant_part}

    def validate_plant_damages(
        self,
        value       : Text,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any],
    ) -> Dict[Text, Any]:
        """Validate slot plant_damages"""

        logger.info('validate_plant_problem_form - validate_plant_damages - START')
        logger.info(f'validate_plant_problem_form - validate_plant_damages - SLOT VALUE: {value}')
        
        plant_damages = []
        if value: plant_damages = value        
        else: dispatcher.utter_message(
            text = 'These kind of plant damages is not recognized. '\
                'Press button "I don\'t know" if you don\'t know '\
                'the plant damages.')
        
        logger.info('validate_plant_problem_form - validate_plant_damages - END')
        return {'plant_damages': plant_damages}

