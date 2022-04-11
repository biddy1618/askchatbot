from typing import Dict, Text, Any, List

from rasa_sdk import Action, Tracker
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


class ActionAskForProblemDescription(Action):
    '''Custom action for slot validation - problem_description.'''
    
    def name(self) -> Text:
        return 'action_ask_problem_description'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:

        logger.info('action_ask_problem_description - START')

        dispatcher.utter_message(text = helper.utterances['ask_problem_desc'])

        logger.info('action_ask_problem_description - END')
        return []


class ValidateProblemDescriptionSlot(Action):
    '''Validating problemdescription slot.'''
    
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
            for entity in tracker.latest_message['entities']:
                print(f'Entity: "{entity["entity"]}"', end = '')
                if 'role'   in entity: print(f', role: "{entity["role"]}"', end = '')
                if 'group'  in entity: print(f', group: "{entity["group"]}"', end = '')
                if 'value'  in entity: print(f', VALUE: "{entity["value"]}"', end = '')
                print('\n')
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
            'pest_location' : tracker.get_slot('pest_location')
        }

        slots_extracted = {s: list(set(slots[s])) for s in slots if slots[s] is not None}
        slots_utterance = '</br>'.join(['<strong>' + k + '</strong>' + ': ' + str(v) for k, v in slots_extracted.items()])
        slots_query     = ' '.join(sum(slots_extracted.values(), []))
        slots_query     = None if slots_query == '' else slots_query
        buttons         = [
            helper.buttons['start_over'     ],
            helper.buttons['request_expert' ]
        ]
        slots_utterance = ''
        entities = []
        for entity in tracker.latest_message['entities']:
            if entity["entity"] in ['action', 'descr', 'location', 'name', 'part', 'type']:
                en_dict = {}
                en_dict['entity'] = entity["entity"]
                if 'value'  in entity: 
                    en_dict['value'] = entity["value"]
                if 'role'   in entity: 
                    en_dict['role'] = entity["role"]
                if 'group'  in entity: 
                    en_dict['group'] = entity["group"]
                found = False
                for d in entities:
                    if d == en_dict:
                        found = True
                if not found:
                    slots_utterance += f'Entity: "{entity["entity"]}"</br>'
                    if 'value'  in entity: 
                        slots_utterance += f', value: "{entity["value"]}"</br>'
                    if 'role'   in entity: 
                        slots_utterance += f', role: "{entity["role"]}"</br>'
                    if 'group'  in entity: 
                        slots_utterance += f', group: "{entity["group"]}"</br>'
                    slots_utterance += '</br></br>'
                    entities.append(en_dict)

        results     = False
        filter_ids  = []
        events      = []
        es_data     = {'slots': slots_extracted, 'filter_ids': filter_ids}

        logger.info(f'action_submit_es_query_form - required problem_description    slot value - {query}')
        for k, v in slots_extracted.items():
            logger.info(f'action_submit_es_query_form - optional {k:<16} slot value - {v}')
        

        if not config.es_imitate:            
            if config.debug:            
                # dispatcher.utter_message(text = 'Extracted slots:</br>' + slots_utterance   )
                dispatcher.utter_message(text = helper.utterances['debug_slots'] + slots_utterance   )
                
                res, filter_ids = await submit(query, slots = slots_query)
                top_n = config.es_top_n
                if len(res['data']) < config.es_top_n:
                    top_n = len(res['data'])
                
                if top_n == 0:
                    # dispatcher.utter_message(text = 'Unfortunately, could not find any results that might help you... Try reducing <strong>es_cut_off</strong> parameter.')
                    dispatcher.utter_message(text = helper.utterances['debug_no_results'])
                else:
                    # message = f'Top {top_n} results.'
                    message = helper.utterances['debug_results'].format(str(top_n))
                    slots_query = None
                    if slots_query:
                        # message = f'Results with slots improvement... Top {top_n} results.'
                        message = helper.utterances['debug_slot_results'].format(str(top_n))
                        dispatcher.utter_message(text = message , json_message = res)
                    results = True

            else:
                res, filter_ids = await submit(query, slots = slots_query)
                
                top_n = config.es_top_n
                if len(res['data']) < config.es_top_n:
                    top_n = len(res['data'])
                
                if top_n == 0:
                    # dispatcher.utter_message(text = 'Unfortunately, could not find any results that might help you... Try to reformulate your problem description, please.')
                    dispatcher.utter_message(text = helper.utterances['no_results'])
                else:
                    dispatcher.utter_message(text = res['text'], json_message = res)
                    results = True
                
            if results:
                es_data['filter_ids'] = filter_ids
                events.append(SlotSet('es_data', es_data))
                # events.append(FollowupAction('es_result_form'))
            else:
                events = helper._reset_slots(tracker)
                events.append(SlotSet('done_query', True))
                dispatcher.utter_message(text = helper.utterances['add_help'], buttons = buttons)
        
        else:
            logger.info(f'action_submit_es_query_form - run - not doing actual ES query')
            events = helper._reset_slots(tracker)
            dispatcher.utter_message(text = helper.utterances['debug_no_es'], buttons = buttons)


        logger.info(f'action_submit_es_query_form - run - END')
        return events

class ActionAskForProblemDescriptionAdd(Action):
    '''Custom action for slot validation - plant_name.'''
    
    def name(self) -> Text:
        return 'action_ask_problem_description_add'
    
    def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:

        logger.info('action_ask_problem_description_add - START')
        es_data = tracker.get_slot('es_data')
        
        required_utterances = {
            'plant_name'    : 'plant name'              ,
            'plant_type'    : 'plant type'              ,
            'plant_part'    : 'plant part'              ,
            'plant_damage'  : 'damage caused to plant'  ,
            'plant_pest'    : 'pest name or description',
            'pest_location' : 'location of pest'
        }

        intent_prev = tracker.latest_message['intent']['name']
        buttons     = []
        message     = ''  
        if intent_prev == 'intent_deny':
            message = helper.utterances['more_details']
        else:
            message = helper.utterances['ask_more_details']
            buttons = [
                helper.buttons['affirm_thanks'  ],
                helper.buttons['deny_details'   ],
                helper.buttons['deny_question'  ],
                helper.buttons['deny_expert'    ],
            ]
        add_detail = False
        if es_data is not None and 'slots' in es_data:
            for s in required_utterances.keys():
                if s not in es_data['slots'].keys():
                    if not add_detail:  message += ' (like ' + required_utterances[s]
                    else:               message += ', ' + required_utterances[s]
                    add_detail = True
        
        if add_detail:  message += ').'
        else:           message += '.'

        dispatcher.utter_message(text = message, buttons = buttons)

        logger.info('action_ask_problem_description_add - END')
        return []
    

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
        if problem_desc_add is not None and problem_desc_add in ['yes', 'expert']:
            for slot in domain_slots:
                if slot != 'problem_description_add': 
                    logger.info(f'validate_es_result_form - removing slot - {slot}')        
                    updated_slots.remove(slot)
        elif problem_desc_add is not None:
            for slot in domain_slots:
                if slot not in tracker.slots_to_validate(): 
                    logger.info(f'validate_es_result_form - removing slot - {slot}')        
                    updated_slots.remove(slot)
        
        logger.info(f'validate_es_result_form - updated slots    - {updated_slots}')
        logger.info(f'validate_es_result_form - required slots   - END')

        return updated_slots
    
    def validate_problem_description_add(
        self,
        value       : Text,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any],
    ) -> Dict[Text, Any]:
        '''Validate slot problem_description_add.'''

        logger.info('validate_problem_description_add - validate_problem_description_add - START')
        logger.info(f'validate_problem_description_add - validate_problem_description_add - slot value - {value}')

        problem_description_add = None
        if value != 'no':
            problem_description_add = value
            
        logger.info('validate_problem_description_add - validate_plant_type - END')
        return {'problem_description_add': problem_description_add}


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

        query = tracker.get_slot('problem_description_add')
        logger.info(f'action_submit_es_result_form - required problem_description_add slot value - {query}')

        if query == 'expert':
            dispatcher.utter_message(text = helper.utterances['connect_expert'], buttons = [helper.buttons['start_over']])
            events = helper._reset_slots(tracker)
            events.append(SlotSet('done_query', True))

            return events
        
        elif query != 'yes':
            es_data = tracker.get_slot('es_data')
            
            slots = {
                'plant_name'    : tracker.get_slot('plant_name'   ),
                'plant_type'    : tracker.get_slot('plant_type'   ),
                'plant_part'    : tracker.get_slot('plant_part'   ),
                'plant_damage'  : tracker.get_slot('plant_damage' ),
                'plant_pest'    : tracker.get_slot('plant_pest'   ),
                'pest_location' : tracker.get_slot('pest_location' )
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
            
            for k, v in slots_extracted.items():
                logger.info(f'action_submit_es_result_form - optional {k:<16} slot value - {v}')
            
            if config.debug:            
                dispatcher.utter_message(text = helper.utterances['debug_slots'] + slots_utterance   )
                
                res, _ = await submit(query, slots = slots_query, filter_ids = filter_ids)
                top_n = config.es_top_n
                if len(res['data']) < config.es_top_n:
                    top_n = len(res['data'])
                
                if top_n == 0:
                    dispatcher.utter_message(text = helper.utterances['debug_no_results'])
                else:
                    message = helper.utterances['debug_results'].format(str(top_n))
                    if slots_query:
                        message = helper.utterances['debug_slot_results'].format(str(top_n))
                        dispatcher.utter_message(text = message , json_message = res)

            else:
                res, _ = await submit(query, slots = slots_query, filter_ids = filter_ids)
                
                top_n = config.es_top_n
                if len(res['data']) < config.es_top_n:
                    top_n = len(res['data'])
                
                if top_n == 0:  dispatcher.utter_message(text = helper.utterances['no_results'])
                else:
                    dispatcher.utter_message(text = res['text'], json_message = res)

        buttons = [
            helper.buttons['start_over'     ],
            helper.buttons['request_expert' ]
        ]
        dispatcher.utter_message(text = helper.utterances['add_help'], buttons = buttons)
        events = helper._reset_slots(tracker)
        events.append(SlotSet('done_query', True))

        logger.info(f'action_submit_es_result_form - run - END')
        return events
