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

    async def extract_problem_details(
        self, 
        dispatcher  : CollectingDispatcher  , 
        tracker     : Tracker               , 
        domain      : Dict
    ) -> Dict[Text, Any]:
        '''Custom extraction function for problem_details entity-slot mapping.'''
        
        logger.info(f'validate_es_query_form - extract_problem_details - START')
        logger.info(f'validate_es_query_form - extract_problem_details - prev. intent - {tracker.get_intent_of_latest_message()}')

        slots = helper._get_entity_groups(tracker.latest_message['entities'])
        
        for g, roles in slots.items():
            logger.info(f'validate_es_query_form - extract_problem_details - entity group   - {g}')
            if 'pest'   in roles:
                for e in roles['pest'   ]: logger.info(f'validate_es_query_form - extract_problem_details - pest related   - (entity: {e[1]}, value: {e[2]})')
            if 'damage' in roles:
                for e in roles['damage' ]: logger.info(f'validate_es_query_form - extract_problem_details - damage related - (entity: {e[1]}, value: {e[2]})')
            if 'plant'  in roles:
                for e in roles['plant'  ]: logger.info(f'validate_es_query_form - extract_problem_details - plant related  - (entity: {e[1]}, value: {e[2]})')

        logger.info(f'validate_es_query_form - extract_problem_details - END')
        
        return {'problem_details': slots}


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

        query = tracker.get_slot('problem_description'  )
        slots = tracker.get_slot('problem_details'      )
        
        logger.info(f'action_submit_es_query_form - required problem_description    slot value - {query}')
        for g, roles in slots.items():
            logger.info(f'action_submit_es_query_form - optional slots - slot group - {g}')
            for r, ents in roles.items():
                for e in ents:
                    logger.info(f'action_submit_es_query_form - optional slots - role: {r} - {e[1]}: {e[2]}')

        results     = False
        filter_ids  = []
        events      = []
        es_data     = {'slots': slots, 'filter_ids': filter_ids}
        buttons     = [
            helper.buttons['start_over'     ],
            helper.buttons['request_expert' ]
        ]

        
        slots_utterance, slots_query = helper._process_slots(slots)
        
        if slots_query is not None:
            for q in slots_query:
                logger.info(f'action_submit_es_query_form - slot query - {q}')

        
        if not config.es_imitate:            
            if config.debug:            
                dispatcher.utter_message(text = helper.utterances['debug_slots'] + slots_utterance)
                
                res, filter_ids = await submit(query, slots = slots_query)
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
                    results = True

            else:
                res, filter_ids = await submit(query, slots = slots_query)
                
                top_n = config.es_top_n
                if len(res['data']) < config.es_top_n:
                    top_n = len(res['data'])
                
                if top_n == 0:
                    dispatcher.utter_message(text = helper.utterances['no_results'])
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

    async def extract_problem_details(
        self, 
        dispatcher  : CollectingDispatcher  , 
        tracker     : Tracker               , 
        domain      : Dict
    ) -> Dict[Text, Any]:
        '''Custom extraction function for problem_details entity-slot mapping.'''
        
        logger.info(f'validate_es_result_form - extract_problem_details - START')
        logger.info(f'validate_es_result_form - extract_problem_details - prev. intent - {tracker.get_intent_of_latest_message()}')

        slots = helper._get_entity_groups(tracker.latest_message['entities'])
        
        for g, roles in slots.items():
            logger.info(f'validate_es_result_form - extract_problem_details - entity group   - {g}')
            if 'pest'   in roles:
                for e in roles['pest'   ]: logger.info(f'validate_es_result_form - extract_problem_details - pest related   - (entity: {e[1]}, value: {e[2]})')
            if 'damage' in roles:
                for e in roles['damage' ]: logger.info(f'validate_es_result_form - extract_problem_details - damage related - (entity: {e[1]}, value: {e[2]})')
            if 'plant'  in roles:
                for e in roles['plant'  ]: logger.info(f'validate_es_result_form - extract_problem_details - plant related  - (entity: {e[1]}, value: {e[2]})')

        logger.info(f'validate_es_result_form - extract_problem_details - END')
        
        return {'problem_details': slots}
    
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
        slots = tracker.get_slot('problem_details')
        
        logger.info(f'action_submit_es_result_form - required problem_description_add slot value - {query}')
        for g, roles in slots.items():
            logger.info(f'action_submit_es_query_form - optional slots - slot group - {g}')
            for r, ents in roles.items():
                for e in ents:
                    logger.info(f'action_submit_es_query_form - optional slots - role: {r} - {e[1]}: {e[2]}')

        if query == 'expert':
            dispatcher.utter_message(text = helper.utterances['connect_expert'], buttons = [helper.buttons['start_over']])
            events = helper._reset_slots(tracker)
            events.append(SlotSet('done_query', True))

            return events
        
        elif query != 'yes':
            
            es_data             = tracker.get_slot('es_data')
            prev_slots          = es_data['slots']
            filter_ids          = es_data['filter_ids']            
            events              = []

            _, prev_slots                   = helper._process_slots(es_data['slots'])
            slots_utterance, slots_query    = helper._process_slots(slots, prev_slots = prev_slots)
            
            if config.debug:            
                dispatcher.utter_message(text = helper.utterances['debug_slots'] + slots_utterance)
                
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
