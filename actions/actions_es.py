from re import A
from typing import Dict, Text, Any, List, Union, Optional


from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction, ValidationAction
from rasa_sdk.events import (
    SlotSet,
    EventType
)

import json

from actions.es import config
from actions.es.es import submit

import logging
logger = logging.getLogger(__name__)

import inflect
inflecter = inflect.engine()
    
class ValidateESQueryForm(FormValidationAction):
    '''Query the ES Knowledge Base.'''

    def name(self) -> Text:
        return 'validate_es_query_form'

    # async def required_slots(
    #     self,
    #     domain_slots: List[Text],
    #     dispatcher  : CollectingDispatcher,
    #     tracker     : Tracker,
    #     domain      : Dict[Text, Any],
    #     ) -> List[Text]:
    #     '''A list of required slots that the form has to fill.'''

    #     logger.info('validate_es_query_form - required slots - START')
        

    #     updated_slots = domain_slots.copy()
        
    #     if tracker.get_slot('pest_causes_damage') == 'no':
    #         updated_slots.remove('pest_damage_description')
        
    #     logger.info(f'validate_es_query_form - required slots - {updated_slots}')
    #     logger.info(f'validate_es_query_form - required slots - END')

    #     return updated_slots

    # def validate_plant_type(
    #     self,
    #     value       : Text,
    #     dispatcher  : CollectingDispatcher,
    #     tracker     : Tracker,
    #     domain      : Dict[Text, Any],
    # ) -> Dict[Text, Any]:
    #     '''Validate slot plant_type.'''

    #     logger.info('validate_plant_problem_form - validate_plant_type - START')
    #     logger.info(f'validate_plant_problem_form - validate_plant_type - SLOT VALUE: {value}')

    #     plant_type = None
    #     if value: plant_type = value
    #     else: dispatcher.utter_message(
    #         text = 'This kind of plant type is not recognized. '\
    #             'Press button "I don\'t know" if you don\'t know '\
    #             'the plant type.')
        
    #     logger.info('validate_plant_problem_form - validate_plant_type - END')
    #     return {'plant_type': plant_type}
    def validate_problem_description(
        self,
        value       : Text,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any],
    ) -> Dict[Text, Any]:

        plant_name          = next(tracker.get_latest_entity_values('plant_damage'       ), None)
        plant_type          = next(tracker.get_latest_entity_values('plant_type'         ), None)
        plant_part          = next(tracker.get_latest_entity_values('plant_part'         ), None)
        plant_damage        = next(tracker.get_latest_entity_values('plant_damage'       ), None)
        plant_pest          = next(tracker.get_latest_entity_values('plant_pest'         ), None)
        logger.info(f'action_submit_es_query_form - required problem_description slot value - {value}')
        logger.info(f'action_submit_es_query_form - optional plant_name slot value - {plant_name}'                  )
        logger.info(f'action_submit_es_query_form - optional plant_type slot value - {plant_type}'                  )
        logger.info(f'action_submit_es_query_form - optional plant_part slot value - {plant_part}'                  )
        logger.info(f'action_submit_es_query_form - optional plant_damage slot value - {plant_damage}'              )
        logger.info(f'action_submit_es_query_form - optional plant_pest slot value - {plant_pest}'                  )

    
        return [SlotSet('problem_description', value)]



class ActionSubmitESQueryForm(Action):
    '''Custom action for submitting form - action_submit_es_query_form.'''
    
    def name(self) -> Text:
        return 'action_submit_es_query_form'
    
    async def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any],
    ) -> List[Dict]:
        '''Define what the form has to do after all required slots are filled.'''

        logger.info(f'action_submit_es_query_form - run - START')

        problem_description = tracker.get_slot('problem_description')
        plant_name          = tracker.get_slot('plant_damage'       )
        plant_type          = tracker.get_slot('plant_type'         )
        plant_part          = tracker.get_slot('plant_part'         )
        plant_damage        = tracker.get_slot('plant_damage'       )
        plant_pest          = tracker.get_slot('plant_pest'         )

        logger.info(f'action_submit_es_query_form - required problem_description slot value - {problem_description}')
        logger.info(f'action_submit_es_query_form - optional plant_name slot value - {plant_name}'                  )
        logger.info(f'action_submit_es_query_form - optional plant_type slot value - {plant_type}'                  )
        logger.info(f'action_submit_es_query_form - optional plant_part slot value - {plant_part}'                  )
        logger.info(f'action_submit_es_query_form - optional plant_damage slot value - {plant_damage}'              )
        logger.info(f'action_submit_es_query_form - optional plant_pest slot value - {plant_pest}'                  )

        logger.info(f'action_submit_es_query_form - run - START')
        
        if not config.es_imitate:
            res_problems, res_information, res_ask = await submit(
                problem_description
            )

            buttons = [
                {'title': 'Start over',             'payload': '/intent_greet'          },
                {'title': 'Connect me to expert',   'payload': '/intent_request_expert' }
            ]

            
            dispatcher.utter_message(text = res_problems['text']    , json_message = res_problems               )
            dispatcher.utter_message(text = res_information['text'] , json_message = res_information            )
            dispatcher.utter_message(text = res_ask['text']         , json_message = res_ask, buttons = buttons )

        else:
            message = "Not doing an actual elastic search query."
            dispatcher.utter_message(message)

        return [SlotSet('done_query', True)]