from typing import Dict, Text, Any, List


from rasa_sdk import Action, Tracker, ValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import (
    SlotSet,
    FollowupAction,
    EventType
)

from actions import helper

from actions.es import config
from actions.es.es import submit

import logging
logger = logging.getLogger(__name__)

import inflect
inflecter = inflect.engine()


class ValidateProblemDescriptionSlot(Action):
    
    def name(self) -> Text:
        return 'action_validate_problem_description'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher  ,
        tracker     : Tracker               ,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:
        '''Validate problem_description slot.'''
        
        logger.info('action_validate_problem_description - START')
        message = tracker.latest_message
        events = []

        if message['intent']['name'] == 'intent_problem_description' and \
            (tracker.active_loop_name is None or tracker.active_loop_name != 'es_result_form'):
            
            logger.info('action_validate_problem_description - setting the slot by message value')
            events.append(SlotSet('problem_description', message['text']))
        
        logger.info('action_validate_problem_description - END')
        return events

class ValidateESQueryForm(FormValidationAction):
    '''Validating the ES query form.'''

    def name(self) -> Text:
        return 'validate_es_query_form'

    async def required_slots(
        self,
        domain_slots: List[Text]            ,
        dispatcher  : CollectingDispatcher  ,
        tracker     : Tracker               ,
        domain      : Dict[Text, Any]       ,
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

        query = tracker.get_slot('problem_description')
        slots = {
            'plant_name'    : tracker.get_slot('plant_name'   ),
            'plant_type'    : tracker.get_slot('plant_type'   ),
            'plant_part'    : tracker.get_slot('plant_part'   ),
            'plant_damage'  : tracker.get_slot('plant_damage' ),
            'plant_pest'    : tracker.get_slot('plant_pest'   ),
            'pest_target'   : tracker.get_slot('pest_target' )
        }

        slots_extracted = {s: list(set(slots[s])) for s in slots if slots[s] is not None}
        slots_utterance = '</br>'.join(['<strong>' + k + '</strong>' + ': ' + str(v) for k, v in slots_extracted.items()])
        slots_query     = ' '.join(sum(slots_extracted.values(), []))
        slots_query     = None if slots_query == '' else slots_query
        buttons         = [
            {'title': 'Start over',             'payload': '/intent_greet'          },
            {'title': 'Connect me to expert',   'payload': '/intent_request_expert' }
        ]

        results     = False
        filter_ids  = []
        events      = []
        es_data     = {'slots': slots_extracted, 'filter_ids': filter_ids}

        logger.info(f'action_submit_es_query_form - required problem_description    slot value - {query}')
        for k, v in slots_extracted.items():
            logger.info(f'action_submit_es_query_form - optional {k:<16} slot value - {v}')
        

        if not config.es_imitate:            
            if config.debug:            
                dispatcher.utter_message(text = 'Extracted slots:</br>' + slots_utterance   )
                
                res, _ = await submit(query)
                top_n = config.es_top_n
                if len(res['data']) < config.es_top_n:
                    top_n = len(res['data'])
                
                if top_n == 0:
                    dispatcher.utter_message(text = 'Unfortunately, could not find any results that might help you... Try reducing <strong>es_cut_off</strong> parameter.')
                else:
                    dispatcher.utter_message(text = f'Results without slots improvement... Top {top_n} results.' , json_message = res)
                    results = True

                    if slots_query:
                        res_slots, filter_ids = await submit(query, slots = slots_query)
                    
                        top_n = config.es_top_n
                        if len(res_slots['data']) < config.es_top_n:
                            top_n = len(res_slots['data'])
                        
                        if top_n == 0:
                            dispatcher.utter_message(text = 'Unfortunately, could not find any results for <strong>slots</strong> that might help you... Try reducing <strong>es_cut_off</strong> parameter.')
                        else:
                            dispatcher.utter_message(text = f'Results with slots improvement... Top {top_n} results', json_message = res_slots)
                    
                    else:
                        dispatcher.utter_message(text = f'No slots were extracted... No results for slots.')
            else:
                res, filter_ids = await submit(query, slots = slots_query)
                
                top_n = config.es_top_n
                if len(res['data']) < config.es_top_n:
                    top_n = len(res['data'])
                
                if top_n == 0:  dispatcher.utter_message(text = 'Unfortunately, could not find any results that might help you... Try to reformulate your problem description, please.')
                else:
                    dispatcher.utter_message(text = res['text'], json_message = res)
                    results = True
                
            if results:
                es_data['filter_ids'] = filter_ids
                events.append(SlotSet('es_data', es_data))
                events.append(FollowupAction('es_result_form'))
            else:
                events = helper._reset_slots(tracker)
                events.append(SlotSet('done_query', True))
                dispatcher.utter_message(text = 'Anything else I can help with?', buttons = buttons)
        
        else:
            logger.info(f'action_submit_es_query_form - run - not doing actual ES query')
            dispatcher.utter_message(text = 'Not doing an actual elastic search query.', buttons = buttons)


        logger.info(f'action_submit_es_query_form - run - END')
        return events


class ValidateESResultForm(FormValidationAction):
    '''Validating ES result form.'''

    def name(self) -> Text:
        return 'validate_es_result_form'

    async def required_slots(
        self,
        domain_slots: List[Text]            ,
        dispatcher  : CollectingDispatcher  ,
        tracker     : Tracker               ,
        domain      : Dict[Text, Any]       ,
        ) -> List[Text]:
        '''A list of required slots that the form has to fill.'''

        logger.info('validate_es_result_form - required slots - START')

        updated_slots = domain_slots.copy()
        logger.info(f'validate_es_result_form - required_slots   - {updated_slots                }')
        logger.info(f'validate_es_result_form - slots recognized - {tracker.slots_to_validate()  }')

        problem_desc_add = tracker.get_slot('problem_description_add')
        if problem_desc_add is not None and problem_desc_add == 'yes':
            for slot in domain_slots:
                if slot != 'problem_description_add': 
                    logger.info(f'validate_es_result_form - removing slot - {slot}')        
                    updated_slots.remove(slot)
        elif problem_desc_add is not None and problem_desc_add != 'no':
            for slot in domain_slots:
                if slot not in tracker.slots_to_validate(): 
                    logger.info(f'validate_es_result_form - removing slot - {slot}')        
                    updated_slots.remove(slot)
        
        logger.info(f'validate_es_result_form - updated slots    - {updated_slots}')
        logger.info(f'validate_es_result_form - required slots   - END')

        return updated_slots

class ActionSubmitESResultForm(Action):
    '''Custom action for submitting form - action_submit_es_result_form.'''
    
    def name(self) -> Text:
        return 'action_submit_es_result_form'
    
    async def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any],
    ) -> List[Dict]:
        '''Define what the form has to do after all required slots are filled.'''

        logger.info(f'action_submit_es_result_form - run - START')

        query_more  = tracker.get_slot('query_more')
        query       = None
        logger.info(f'action_submit_es_result_form - required query_more                slot value - {query_more  }')

        if query_more == 'yes':
            query   = tracker.get_slot('problem_description_add')
            es_data = tracker.get_slot('es_data'               )
            
            slots = {
                'plant_name'    : tracker.get_slot('plant_name'   ),
                'plant_type'    : tracker.get_slot('plant_type'   ),
                'plant_part'    : tracker.get_slot('plant_part'   ),
                'plant_damage'  : tracker.get_slot('plant_damage' ),
                'plant_pest'    : tracker.get_slot('plant_pest'   ),
                'pest_target'   : tracker.get_slot('pest_target' )
            }
            slots_extracted = {s: list(set(slots[s])) for s in slots if slots[s] is not None}
            slots_utterance = '</br>'.join(['<strong>' + k + '</strong>' + ': ' + str(v) for k, v in slots_extracted.items()])
            for k, v in slots_extracted.items():
                if k in es_data['slots']:
                    es_data['slots'][k].extend(v)
                    es_data['slots'][k] = list(set(es_data['slots'][k]))
                else:
                    es_data['slots'][k] = v
            slots_extracted = es_data['slots']
            slots_query     = ' '.join(sum(slots_extracted.values(), []))
            slots_query     = None if slots_query == '' else slots_query
            
            filter_ids  = es_data['filter_ids']            
            events      = []
            

            logger.info(f'action_submit_es_result_form - required problem_description    slot value - {query}')
            for k, v in slots_extracted.items():
                logger.info(f'action_submit_es_result_form - optional {k:<16} slot value - {v}')


            dispatcher.utter_message(text = 'Working on your request...')
                        
            if not config.es_imitate:    
                if config.debug:            
                    dispatcher.utter_message(text = 'Extracted slots:</br>' + slots_utterance   )
                    res, _ = await submit(query, filter_ids = filter_ids)
                    top_n = config.es_top_n
                    if len(res['data']) < config.es_top_n:
                        top_n = len(res['data'])
                    
                    if top_n == 0:
                        dispatcher.utter_message(text = 'Unfortunately, could not find any results that might help you... Try reducing <strong>es_cut_off</strong> parameter.')
                    else:
                        dispatcher.utter_message(text = f'Results without slots improvement... Top {top_n} results.' , json_message = res)

                        if slots_query:
                            res_slots, _ = await submit(query, slots = slots_query, filter_ids = filter_ids)
                        
                            top_n = config.es_top_n
                            if len(res_slots['data']) < config.es_top_n:
                                top_n = len(res_slots['data'])
                            
                            if top_n == 0:
                                dispatcher.utter_message(text = 'Unfortunately, could not find any results for <strong>slots</strong> that might help you... Try reducing <strong>es_cut_off</strong> parameter.')
                            else:
                                dispatcher.utter_message(text = f'Results with slots improvement... Top {top_n} results', json_message = res_slots)
                        
                        else:
                            dispatcher.utter_message(text = f'No slots were extracted... No results for slots.')
                else:
                    res, _ = await submit(query, slots = slots_query, filter_ids = filter_ids)
                    
                    top_n = config.es_top_n
                    if len(res['data']) < config.es_top_n:
                        top_n = len(res['data'])
                    
                    if top_n == 0:  dispatcher.utter_message(text = 'Unfortunately, could not find any results that might help you...')
                    else:
                        dispatcher.utter_message(text = res['text'], json_message = res)
            else:
                logger.info(f'action_submit_es_result_form - run - not doing actual ES query')
                dispatcher.utter_message(text = 'Not doing an actual elastic search query.')
        
        buttons         = [
            {'title': 'Start over',             'payload': '/intent_greet'          },
            {'title': 'Connect me to expert',   'payload': '/intent_request_expert' }
        ]
        dispatcher.utter_message(text = 'Anything else I can help with?', buttons = buttons)
        events = helper._reset_slots(tracker)
        events.append(SlotSet('done_query', True))

        logger.info(f'action_submit_es_result_form - run - END')
        return events

'''
i)      DONE    add additional slot - location
ii)     DONE    remove block of triplet and instead provide 1, and ask for the feedback
iii)    DONE    sequential search - based on the query text (filter out)
iv)     try asking additional details on the slots - proactive slot filling
v)      implement the search based on decision tree
vi)     DONE    implement out of the scope intent
    *)  don't use curse words on me, please
vii)    DONE    cut off score for the...
viii)   DONE    make the cut off score configurable...
    *)  
iv)     DONE    follow-up question

For presentation:
Prepare for demo:
    Prepare set of questions
    Show capabilities
    Out-of-scope
    Success

The words in the questions
Synonyms - lady beetle
Common names
Return query that is most close without any real examples.


Introdu

'''