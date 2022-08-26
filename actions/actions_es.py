from typing import Dict, Text, Any, List

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import (
    SlotSet,
    FollowupAction,
    EventType
)

from elasticsearch import RequestError

from actions import helper
from async_timeout import timeout
from actions.es import config
from actions.es.es import submit, save_chat_logs
from actions.es.es_ask_kb import get_total_documents, retrieve_last_update, update_kb
import logging
from datetime import datetime
from threading import Thread
import asyncio 
import uvloop

# from threading import Thread
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

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
        events      = []
        es_data     = {'query': query, 'slots': slots}
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
                res, debug_query = await submit(query, slots = slots_query)
                dispatcher.utter_message(text = helper.utterances['debug_query'].format(debug_query))
                
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
                res, _ = await submit(query, slots = slots_query)
                
                top_n = config.es_top_n
                if len(res['data']) < config.es_top_n:
                    top_n = len(res['data'])

                if top_n == 0:
                    dispatcher.utter_message(text = helper.utterances['no_results'])
                else:
                    dispatcher.utter_message(text = helper.utterances['results'])
                    dispatcher.utter_message(text = res['text'], json_message = res)
                    results = True
                
            if results:
                top_score = float(res['data'][0]['score'])
                if top_score >= 0.6 and len(query.split()) > 6:
                    events = helper._reset_slots(tracker)
                    events.append(SlotSet('done_query', True))
                    dispatcher.utter_message(text = helper.utterances['add_help'], buttons = buttons)
                else:
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
            add_details = helper._get_add_message(es_data)
            if add_details: logger.info(f'action_ask_problem_description_add - additional message - {add_details}')
            message += add_details
        
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
            prev_query          = es_data['query']
            prev_slots          = es_data['slots']
            events              = []

            _, prev_slots                   = helper._process_slots(es_data['slots'])
            slots_utterance, slots_query    = helper._process_slots(slots, prev_slots = prev_slots)
            query                           = '. '.join([prev_query, query])
            
            if config.debug:            
                dispatcher.utter_message(text = helper.utterances['debug_slots'] + slots_utterance)
                res, debug_query = await submit(query, slots = slots_query)
                dispatcher.utter_message(text = helper.utterances['debug_query'].format(debug_query))
                
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
                res, _ = await submit(query, slots = slots_query)
                
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


class ActionSaveConversation(Action):
    '''Action for saving conversation.'''

    def name(self) -> Text:
        return 'action_save_conversation'
    
    async def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
    ) -> List[EventType]:
        
        logger.info('action_save_conversation - START')
        
        chat_history = helper._parse_tracker_events(tracker.events)
        export = {
            'chat_id'       : tracker.sender_id             ,
            'timestamp'     : chat_history[0]['timestamp']  ,
            'chat_history'  : chat_history
        }

        try:
            await save_chat_logs(export)
        except RequestError as e:
            logger.error(f'action_save_conversation - error while indexing - failed to save conversation with chat_id - {export["chat_id"]}')
        except AssertionError as e:
            logger.error(f'action_save_conversation - error on ES side - failed to save conversation with chat_id - {export["chat_id"]}')        
        
        logger.info(f'action_save_conversation - success saving conversation with chat_id - {export["chat_id"]}')
        logger.info('action_save_conversation - END')
        return []


class ActionLastKBUpdate(Action):
    '''Retrieves the last update for Ask Extension Knowledge Base index'''

    def name(self) -> Text:
        return 'action_retrieve_last_kb_update'

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        logger.info('Retrieving last KB update - Start')
        try:
            date = await retrieve_last_update()
            dispatcher.utter_message(text=f'The Ask Extension Knowledge Base was last updated on {date}')
        except RequestError as e:
            logger.error(f'A request error occurred. {e}')
        except Exception as e:
            logger.error(f"An unknown error occurred. {e}")
        logger.info('Knowledge Base updated - End')
        return []

class ActionGetTotalDocuments(Action):
    '''Retrieves the last update for Ask Extension Knowledge Base index'''

    def name(self) -> Text:
        return 'action_get_total_documents'

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        logger.info('Getting total documents in Knowledge base')
        total = await get_total_documents()
        dispatcher.utter_message(text=f'There are currently {total:,} total items in my knowledge base.')
        return []

    
class ActionUpdateKB(Action):
    '''Updates the knowledge base using the last found date'''

    def name(self) -> Text:
        return 'action_update_kb'

    def check_dates(self, start_date, end_date):
        """Simple function to see whether dates are valid and return a message if not. """
        if start_date and end_date:
            logger.info(f"Inputted start date: {start_date}")
            logger.info(f'Inputted end date: {end_date}')
            try: 
                start= [int(i) for i in start_date.split('-')]
                end = [int(i) for i in end_date.split('-')]
                if datetime(year=start[0], month=start[1], day=start[2]) and datetime(year=end[0], month=end[1], day=end[2]):
                    if datetime(year=start[0], month=start[1], day=start[2]) < datetime(year=end[0], month=end[1], day=end[2]):
                        return start_date, end_date, ""
                else:
                    return None, None, "I'm detecting that the start date came after the end date. Do you mind rephrasing?"
            except Exception as e:
                logger.error(f"Error: {e}")
                return None, None, "The dates inputted are invalid. Do you mind rephrasing?"
        return None, None, "No dates were found"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[EventType]:
        start_date, end_date, msg = self.check_dates(tracker.get_slot('start'), tracker.get_slot('end'))
        if (start_date and end_date) or msg == 'No dates were found':
            logger.info('Knowledge Base update - Start')
            before = await get_total_documents()
            try:
                # Asyncio event loop problems, so just opening new thread...
                task = asyncio.create_task(update_kb(start_date, end_date))
                await task 
                after = await get_total_documents()
                total_added = after - before 
                if total_added == 0:
                    msg = "Looks like there is nothing for me to add."
                else: 
                    msg = f"The update was successful! I've added {total_added:,} items to my brain."
            except:
                msg= "Uh oh. Looks like there was an error when trying to update the knowledge base."

            dispatcher.utter_message(text=msg)
            return [SlotSet('start', None), SlotSet('end', None)]
        else:
            dispatcher.utter_message(text= msg)
            return [SlotSet('start', None), SlotSet('end', None)]