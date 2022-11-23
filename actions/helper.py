'''
Module for helper functions and static variables.

Author: Dauren Baitursyn
'''
import json
from typing import Dict, Text, Any, List, Tuple
from datetime import datetime

from rasa_sdk import Tracker
from rasa_sdk.events import SlotSet, ActionExecuted, UserUttered

from actions.es import config

# Dictionary for parameters debug
params = {
    'search_size'       : int,
    'max_return_amount' : int,
    'cut_off'           : float,
    'ae_downweight'     : float
}

# Utterances
utterances = {
    'greet'                 : "Hi, I'm Scout, the UC IPM Assistant!",
    'goodbye'               : 'Bye!',
    'help'                  : 'How can I help you?',
    'ipm'                   : 'IPM (Integrated Pest Management) is an ecosystem-based strategy that focuses on long-term prevention of pests or their damage through a combination of techniques such as biological control, habitat manipulation, modification of cultural practices, and use of resistant varieties. You can find more details <a href="https://www2.ipm.ucanr.edu/What-is-IPM/" target="_blank">here</a>.',
    'connect_expert'        : f'You can ask one of our experts at <a href="{config.expert_url}" target="_blank">Ask Extension</a>.',
    'iambot'                : 'I am a bot, powered by <a href="https://rasa.com/" target="_blank">Rasa</a> platform. I can help you with the pest-related issues and questions. If you have one, please, describe your problem.',
    'out_of_scope'          : "Sorry, that request is outside my scope. For now, I only deal with pest-related requests.",
    'fallback'              : "I'm sorry, I didn't catch that. Can you rephrase?",
    'ask_problem_desc'      : 'Please describe your problem.',
    'no_results'            : 'Unfortunately, I could not find any results that might help you... Please try to reword your pest problem.',
    'results'               : 'Here is what I found based on your description:',
    'more_details'          : 'Please provide additional information.',
    'ask_more_details'      : 'Did that answer your question? If not, can you give me more information?',
    'add_help'              : 'Anything else I can help with?',
    'ask_more_details_pest' : ' For example, can you tell me where you see {0}, (e.g. is it indoors or outdoors)?',
    'ask_more_details_other': ' For example, have you seen any bugs around the {0}? If so, what do they look like?',
    'ask_more_details_less' : ' For example, what do you need to know about the {0}?',
    'debug_query'           : 'Final transformed query with synonym replacement that was used for retrieval:</br> <i>{0}<i>',
    'debug_slots'           : 'Extracted slots</br>[Format: (<i>relation</i>) <strong>entity</strong> - <strong>value</strong>]:</br>',
    'debug_no_results'      : 'Unfortunately, could not find any results that might help you... Try reducing <strong>es_cut_off</strong> parameter.',
    'debug_results'         : 'Here are my top {0} resources and FAQs. You can scroll through them using the arrow heads on the sides.',
    'debug_slot_results'    : 'Results with slots improvement... Here are my top {0} resources and FAQs. You can scroll through them using the arrow heads on the sides.',
    'debug_no_es'           : 'Not doing an actual elastic search query.',
}

# Buttons
buttons = {
    'ask_question'  : {
        'title'     : 'I would like to ask a pest related question.', 
        'payload'   : '/intent_help_question'
    },
    'learn_ipm'     : {
        'title'     : 'I want to learn more about IPM.', 
        'payload'   : '/intent_explain_ipm'
    },
    'request_expert': {
        'title'     : 'Connect me to an expert.', 
        'payload'   : '/intent_request_expert'
    },
    'start_over'    : {
        'title'     : 'Start over.',
        'payload'   : '/intent_greet'
    },
    'affirm_thanks' : {
        'title'     : 'Yes, thank you!', 
        'payload'   : '/intent_affirm'
    },
    'deny_details'  : {
        'title'     : "No. I'd like to provide additional details.",
        'payload'   : '/intent_deny'
    },
    'deny_question' : {
        'title'     : "No. I'd like to ask different question.", 
        'payload'   : '/intent_affirm'
    },
    'deny_expert'   : {
        'title'     : "No, I'd like to speak to an expert.",
        'payload'   : '/intent_request_expert'
    }
}

# Parameters for fine-tuning
## Entity names and order
entity_order = {
    'descr'     : 1,
    'type'      : 2,
    'name'      : 3,
    'part'      : 4,
    'action'    : 5,
    'location'  : 6
}

## Role order
role_order = ['pest', 'plant', 'damage', 'remedy']


def _reset_slots(tracker: Tracker) -> List[Any]:
    '''Clean up slots from all previous forms.'''
    
    events = []

    for k, _ in tracker.slots.items():
        if k in ['shown_greeting', 'shown_privacy_policy']: 
            events.append(SlotSet(k, True))
        elif k in ['shown_explain_ipm', 'done_query']:
            continue
        else: 
            events.append(SlotSet(k, None))

    return events


def _next_intent(next_intent: Text) -> List[Dict]:
    '''Add next intent events, mimicking a prediction by NLU.'''
    return [
        ActionExecuted("action_listen"),
        UserUttered(
            '/' + next_intent,
            {'intent': {'name': next_intent, 'confidence': 1.0}, 'entities': {}},
        )
    ]



def _parse_config_message(text: str) -> Tuple[str, str]:
    '''Parse the configuration parameters from user (only debug mode).'''
    parameter, value = None, None
    try:
        _, parameter, value = [t for t in text.split()]
        if parameter in params  : value = params[parameter](value)
        else                    : raise Exception  
    except Exception:
        parameter, value = None, None
    return parameter, value


def _get_config_message(config):
    '''Get the configuration message (only in debug mode).'''
    message = (
        'Bot Configuration:</br>'
        f'Stage: {config.stage}</br>'
        f'<strong>expert_url <i>{config.expert_url}</i></strong></br>'
        f'<strong>search_size <i>{config.search_size}</i></strong></br>'
        f'<strong>cut_off <i>{config.cut_off}</i></strong></br>'
        f'<strong>max_return_amount <i>{config.max_return_amount}</i></strong></br>'
        f'<strong>ae_downweight <i>{config.ae_downweight}</i></strong></br></br>'
        'To change the configuration parameters, use following schema:</br>'
        'parameter <i>param_name value</i></br>'
        '(i.e. <strong>parameter cut_off <i>0.5</i></strong>)'
    )

    return message


def _get_entity_groups(entities):
    '''Get the entity groups from the user's message.'''
    ent_list = []

    for entity in entities:
        if entity["entity"] in entity_order.keys() and 'role' in entity and 'group' in entity:
            en_dict = {}
            en_dict['entity'] = entity['entity' ]
            en_dict['value' ] = entity['value'  ]
            en_dict['role'  ] = entity['role'   ]
            en_dict['group' ] = entity['group'  ]
            
            ent_list.append(en_dict)

    ent_list = [i for n, i in enumerate(ent_list) if i not in ent_list[n + 1:]]

    slots = {}
    for e in ent_list:
        g = e.pop('group')
        e_tuple = (entity_order[e['entity']], e['entity'], e['value'].lower())
        if g in slots:
            r = e['role']
            if r in slots[g]: slots[g][r].append(e_tuple) 
            else            : slots[g][r] = [e_tuple]
        else: slots[g] = {e['role']: [e_tuple]}

    for g in slots.values():
        for r in g:
            g[r] = sorted(g[r], key = lambda x: x[0])

    return slots

def _get_add_message(es_data):
    '''Get message for additional message regarding pests and location of the entities.'''
    
    # check if pest entity exists
    def _get_pest(slots):

        pest_entity = None
        for group in slots.values():
            if 'pest' in group:
                for entity in group.get('pest'):
                    if entity[1] in ['name', 'type', 'part']:
                        pest_entity = entity[2]
                        break
                else:
                    continue
                break
        
        return pest_entity
    
    # check if location entity exists
    def _get_location(slots):

        location_entity = None
        for group in slots.values():
            for role in group.values():
                for entity in role:
                    if entity[1] in ['location']:
                        location_entity = entity[2]
                        break
                else:
                    continue
                break
            else:
                continue
            break
        
        return location_entity
    
    def _get_plant_or_damage(slots):

        plant_or_damage_entity = None
        for group in slots.values():
            for entity in group.get('plant', []):
                if entity[1] in ['name', 'type', 'part', 'location']:
                    plant_or_damage_entity = entity[2]
                    break
            else:
                for entity in group.get('damage', []):
                    if entity[1] in ['name', 'type', 'part', 'location']:
                        plant_or_damage_entity = entity[2]
                        break
                else:
                    continue
                break
            break
        
        return plant_or_damage_entity

    
    slots = es_data['slots'] if es_data is not None and 'slots' in es_data else {}
    query = es_data['query']
    pest_entity     = _get_pest(slots)
    location_entity = _get_location(slots)
    other_entity    = _get_plant_or_damage(slots)
    message         = ''
    if len(query.split()) <= 6:
        if pest_entity:
            message = utterances['ask_more_details_less'].format(pest_entity)
        elif other_entity:
            message = utterances['ask_more_details_less'].format(other_entity)
    elif pest_entity and not location_entity:
        message = utterances['ask_more_details_pest'].format(pest_entity)
    elif not pest_entity and other_entity:
        message = utterances['ask_more_details_other'].format(other_entity)
    
    return message


def _process_slots(slots, prev_slots = None):
    '''Get slots utterance and compose slots query.'''
    slots_utterance = ''
    for g, roles in slots.items():
        slots_utterance += f'Group {g}:</br>'
        for r, entities in roles.items():
            for e in entities:
                slots_utterance += f'(<i>{r}</i>) <strong>{e[1]}</strong> - <strong>{e[2]}</strong></br>'
        slots_utterance += '</br>'
    
    slots_query = []
    if prev_slots is not None:
        slots_query = prev_slots
    for g, roles in slots.items():
        query = []
        for r in role_order:
            if r in roles:
                query.extend(roles[r])
        slots_query.append(' '.join([e[2] for e in query]))
    
    if len(slots_query) > 0:
        slots_utterance += f'Composed {len(slots_query)} additional queries:</br>'
        for i, q in enumerate(slots_query):
            slots_utterance += f'{i+1}) <i>{q}</i></br>'
    else: slots_query = None
    
    return slots_utterance, slots_query


def _parse_tracker_events(events):
    '''Parse chat history - filtering in only `bot` and `user` events.'''
    chat_history = []

    for event in events:
        if event['event'] == 'user':
            '''
            structure:
                agent       keyword
                timestamp   date
                text        match_only_text
                intent      keyword
            '''
            text        = event['text']
            intent      = event['parse_data']['intent']['name']
            timestamp   = datetime.fromtimestamp(event['timestamp']).isoformat()
            chat_history.append({
                'agent'     : 'user'    ,
                'timestamp' : timestamp ,
                'text'      : text      ,
                'intent'    : intent
            })
        elif event['event'] == 'bot':
            '''
            structure:
                agent       keyword
                timestamp   date
                text        match_only_text
                results     nested
                    url         keyword
                    score       keyword
            '''
            text        = event['text']
            timestamp   = datetime.fromtimestamp(event['timestamp']).isoformat()
            
            chat_history.append({
                'agent'     : 'bot'     ,
                'timestamp' : timestamp ,
                'text'      : text      ,
            })

            if event['data']['custom'] is not None:
                results = []
                custom = event['data']['custom']
                for result in custom['data']:
                    url     = result['url'  ]
                    score   = result['score']
                    results.append({
                        'url'   : url,
                        'score' : score
                    })
                chat_history[-1]['results'] = results
    
    return chat_history


def _parse_date(aft_date = None, bfr_date = None):
    '''Parse date for the logging report.'''
    try:
        if aft_date is None:
            aft_date = datetime.min
        else:

            aft_date = datetime.strptime(aft_date, '%d.%m.%Y')
        
        if bfr_date is None:
            bfr_date = datetime.max
        else:
            bfr_date = datetime.strptime(bfr_date, '%d.%m.%Y')

        aft_date = aft_date.isoformat()
        bfr_date = bfr_date.isoformat()

    except (TypeError, ValueError) as e:
        raise(e)
        

    return aft_date, bfr_date


def _set_config(session_config):
    '''Parse config slot for single session.'''
    try:
        if isinstance(session_config, str):
            session_config = json.loads(session_config)
        for param, func in params.items():
            value = func(session_config[param])
            setattr(config, param, value)
    # If no config was passed down then set it to default
    except (TypeError, KeyError) as r:
        return (
            'Error parsing config message: </br>'
            'Please pass the config file in a JSON format as like following</br>'
            '{search_size: 100,</br>'
            ' cut_off: 0.4,</br>'
            ' max_return_amount: 10,</br>'
            ' ae_downweight: 0.8}</br>'
            'Using default configurations...')
    
    return None
    

