from typing import Dict, Text, Any, List


from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import (
    SlotSet,
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

    async def required_slots(
        self,
        domain_slots: List[Text],
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any],
        ) -> List[Text]:
        '''A list of required slots that the form has to fill.'''

        logger.info('validate_es_query_form - required slots - START')

        updated_slots = domain_slots.copy()
        logger.info(f'validate_es_query_form - required_slots   - {updated_slots                }')
        logger.info(f'validate_es_query_form - slots recognized - {tracker.slots_to_validate()  }')

        if tracker.get_slot("problem_description") is not None:
            for slot in domain_slots:
                if slot not in tracker.slots_to_validate(): 
                    logger.info(f'validate_es_query_form - removing slot - {slot}')        
                    updated_slots.remove(slot)
        
        logger.info(f'validate_es_query_form - updated slots    - {updated_slots}')
        logger.info(f'validate_es_query_form - required slots   - END')

        return updated_slots

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
    # def validate_problem_description(
    #     self,
    #     value       : Text,
    #     dispatcher  : CollectingDispatcher,
    #     tracker     : Tracker,
    #     domain      : Dict[Text, Any],
    # ) -> Dict[Text, Any]:

    #     plant_name          = list(tracker.get_latest_entity_values('plant_damage'       ))
    #     plant_type          = list(tracker.get_latest_entity_values('plant_type'         ))
    #     plant_part          = list(tracker.get_latest_entity_values('plant_part'         ))
    #     plant_damage        = list(tracker.get_latest_entity_values('plant_damage'       ))
    #     plant_pest          = list(tracker.get_latest_entity_values('plant_pest'         ))
    #     logger.info(f'validate_es_query_form - required problem_description slot value - {value}')
    #     logger.info(f'validate_es_query_form - optional plant_name slot value - {plant_name}'                  )
    #     logger.info(f'validate_es_query_form - optional plant_type slot value - {plant_type}'                  )
    #     logger.info(f'validate_es_query_form - optional plant_part slot value - {plant_part}'                  )
    #     logger.info(f'validate_es_query_form - optional plant_damage slot value - {plant_damage}'              )
    #     logger.info(f'validate_es_query_form - optional plant_pest slot value - {plant_pest}'                  )

    
    #     return {}



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

        slots = {
            'problem_description' : tracker.get_slot('problem_description'),
            'plant_name'          : tracker.get_slot('plant_name'           ),
            'plant_type'          : tracker.get_slot('plant_type'         ),
            'plant_part'          : tracker.get_slot('plant_part'         ),
            'plant_damage'        : tracker.get_slot('plant_damage'       ),
            'plant_pest'          : tracker.get_slot('plant_pest'         )
        }

        logger.info(f'action_submit_es_query_form - required problem_description    slot value - {slots["problem_description"   ]}')
        logger.info(f'action_submit_es_query_form - optional plant_name             slot value - {slots["plant_name"            ]}')
        logger.info(f'action_submit_es_query_form - optional plant_type             slot value - {slots["plant_type"            ]}')
        logger.info(f'action_submit_es_query_form - optional plant_part             slot value - {slots["plant_part"            ]}')
        logger.info(f'action_submit_es_query_form - optional plant_damage           slot value - {slots["plant_damage"          ]}')
        logger.info(f'action_submit_es_query_form - optional plant_pest             slot value - {slots["plant_pest"            ]}')

        slots_extracted = {s: slots[s] for s in slots if slots[s] is not None and s != 'problem_description'}
        slots_utterance = '</br>'.join(['<strong>' + k + '</strong>' + ': ' + str(list(set(v))) for k, v in slots_extracted.items()])
        
        dispatcher.utter_message(text = 'Working on your request...')
        
        if config.debug:
            dispatcher.utter_message(text = 'Problem statement:</br>'   + slots['problem_description']  )
            dispatcher.utter_message(text = 'Extracted slots:</br>'     + slots_utterance               )
        
        if not config.es_imitate:
            
            res = await submit(slots['problem_description'])

            buttons = [
                {'title': 'Start over',             'payload': '/intent_greet'          },
                {'title': 'Connect me to expert',   'payload': '/intent_request_expert' }
            ]

            dispatcher.utter_message(text = res['text'], json_message = res, buttons = buttons)
        else:
            message = "Not doing an actual elastic search query."
            dispatcher.utter_message(message)

        return [SlotSet('done_query', True)]

'''
i)      add additional slot - location
ii)     remove block of triplet and instead provide 1, and ask for the feedback
iii)    sequential search - based on the query text (filter out)
iv)     try asking additional details on the slots - proactive slot filling
v)      implement the search based on decision tree
vi)     implement out of the scope intent
vii)    
    *)  don't use curse words on me, please
    *)  cut off score for the...
    *)  make the cut off score configurable...
    *)  
'''