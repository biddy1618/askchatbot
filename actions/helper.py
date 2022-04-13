from typing import Dict, Text, Any, List, Tuple

from rasa_sdk import Tracker
from rasa_sdk.events import (
    SlotSet,
    ActionExecuted,
    UserUttered
)

# Dictionary for parameters debug
params = {
    'es_search_size': int,
    'es_top_n'      : int,
    'es_cut_off'    : float,
    'es_ask_weight' : float
}

# Utterances
utterances = {
    'greet'             : "Hi, I'm the AskExtension Assistant!",
    'goodbye'           : 'Bye!',
    'help'              : 'How can I help you?',
    'ipm'               : 'IPM (Integrated Pest Management) is an ecosystem-based strategy that focuses on long-term prevention of pests or their damage through a combination of techniques such as biological control, habitat manipulation, modification of cultural practices, and use of resistant varieties. You can find more details <a href="https://www2.ipm.ucanr.edu/What-is-IPM/" target="_blank">here</a>.',
    'fallback'          : "I'm sorry, I am still learning. Can you rephrase?",
    'out_of_scope'      : "Sorry, I can't handle that request. For now, I can handle pest related requests. Try me.",
    'connect_expert'    : 'You can ask one of our experts at <a href="https://ask2.extension.org/open.php" target="_blank">Ask Extension</a>.',
    'ask_problem_desc'  : 'Please, describe your problem.',
    'no_results'        : 'Unfortunately, could not find any results that might help you... Try to reformulate your problem description, please.',
    'add_help'          : 'Anything else I can help with?',
    'more_details'      : 'Please, give more more information',
    'ask_more_details'  : 'Did that answer your question? If not, can you give me some more information',
    'debug_slots'       : 'Extracted slots</br>[Format: (<i>relation</i>) <strong>entity</strong> - <strong>value</strong>]:</br>',
    'debug_no_results'  : 'Unfortunately, could not find any results that might help you... Try reducing <strong>es_cut_off</strong> parameter.',
    'debug_results'     : 'Top {0} results.',
    'debug_slot_results': 'Results with slots improvement... Top {0} results.',
    'debug_no_es'       : 'Not doing an actual elastic search query.',
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
        'title'     : "No. I’d like to provide additional details.",
        'payload'   : '/intent_deny'
    },
    'deny_question' : {
        'title'     : "No. I’d like to ask different question.", 
        'payload'   : '/intent_affirm'
    },
    'deny_expert'   : {
        'title'     : "No, I'd like to speak to an expert.",
        'payload'   : '/intent_request_expert'
    }
}

# Entity names and order
entity_names = ['action', 'descr', 'location', 'name', 'part', 'type']
entity_order = {
    'descr'     : 1,
    'type'      : 2,
    'name'      : 3,
    'part'      : 4,
    'action'    : 5,
    'location'  : 6
}


def _reset_slots(tracker: Tracker) -> List[Any]:
    '''Clean up slots from all previous forms.'''
    
    events = []

    for k, v in tracker.slots.items():
        if k in ['shown_greeting', 'shown_privacy_policy']: 
            events.append(SlotSet(k, True))
        elif k in ['shown_explain_ipm', 'done_query']:
            events.append(SlotSet(k, v))
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
        _, parameter, value = [t.strip() for t in text.split(' ')]
        if parameter in params  : value = params[parameter](value)
        else                    : raise Exception  
    except Exception:
        parameter, value = None, None
    return parameter, value


def _get_config_message(config):
    '''Get the configuration message (only in debug mode).'''
    message = (
        'Bot Configuration:</br>'
        f'Debug: {config.debug}</br>'
        f'Version: {config.version}</br>'
        f'<strong>es_search_size <i>{config.es_search_size}</i></strong></br>'
        f'<strong>es_cut_off <i>{config.es_cut_off}</i></strong></br>'
        f'<strong>es_top_n <i>{config.es_top_n}</i></strong></br>'
        f'<strong>es_ask_weight <i>{config.es_ask_weight}</i></strong></br></br>'
        'To change the configuration parameters, use following schema:</br>'
        'parameter <i>param_name value</i></br>'
        '(i.e. <strong>parameter es_cut_off <i>0.5</i></strong>)'
    )

    return message


def _get_entity_groups(entities):
    '''Get the entity groups from the user's message.'''
    ent_list = []

    for entity in entities:
        if entity["entity"] in entity_names and 'role' in entity:
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
        e_tuple = (entity_order[e['entity']], e['entity'], e['value'])
        if g in slots:
            r = e['role']
            if r in slots[g]: slots[g][r].append(e_tuple) 
            else            : slots[g][r] = [e_tuple]
        else: slots[g] = {e['role']: [e_tuple]}
    
    for g in slots.values():
        for r in g:
            g[r] = sorted(g[r], key = lambda x: x[0])

    return slots
    

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
        for r in ['pest', 'damage', 'plant']:
            if r in roles:
                query.extend(roles[r])
        slots_query.append(' '.join([e[2] for e in query]))
    
    if len(slots_query) > 0:
        slots_utterance += f'Composed {len(slots_query)} additional queries:</br>'
        for i, q in enumerate(slots_query):
            slots_utterance += f'{i+1}) <i>{q}</i></br>'
    else: slots_query = None
    
    return slots_utterance, slots_query


# def _get_plant_names(
#     plant_type      : Text          = 'other',
#     n               : int           = 10) -> List[Text]:
#     '''Get plant names corresponding to plant type.'''

#     df = db['plant_matches']
#     df = df[df['plant_type'] == plant_type] if plant_type != 'other' else df
    
#     pn = df['plant_name'].drop_duplicates()
#     if pn.shape[0] > n:
#         pn = pn.sample(n)
    
#     return pn.tolist()


# def _get_plant_parts(
#     plant_type      : Text          = 'other',
#     plant_name      : Text          = 'other',
#     n               : int           = 10) -> List[Text]:
#     '''Get plant details corresponding to plant descriptions.'''

#     pp = None
#     df = db['plant_matches']
#     df = df[df['plant_type'] == plant_type] if plant_type != 'other' else df
#     df = df[df['plant_name'] == plant_name] if plant_name != 'other' else df
    
#     pp = df['plant_part'].drop_duplicates()
#     if pp.shape[0] > n:
#         pp = pp.sample(n)

#     return pp.tolist()


# def _get_plant_damages(
#     plant_type      : Text          = 'other',
#     plant_name      : Text          = 'other',
#     plant_part      : Text          = 'other',
#     n               : int           = 10) -> List[Text]:
#     '''Get plant details corresponding to plant descriptions.'''

#     pd = []
#     df = db['plant_matches']
#     df = df[df['plant_type'] == plant_type] if plant_type != 'other' else df
#     df = df[df['plant_name'] == plant_name] if plant_name != 'other' else df
#     df = df[df['plant_part'] == plant_part] if plant_part != 'other' else df
    
#     pd = df['plant_damage'].drop_duplicates()
#     if pd.shape[0] > n:
#         pd = pd.sample(10)
    
#     return pd.tolist()


# def _jaccard_coef(s1: set, s2: set) -> float:  
#     return len(s1.intersection(s2)) / len(s1.union(s2))


# def _get_problem_links(
#     plant_type      : Text = 'other',
#     plant_name      : Text = 'other',
#     plant_part      : Text = 'other',
#     plant_damages   : List[Text] = []) -> List[Text]:
#     '''Get information associated with plant problem descriptions.'''

#     df = db['plant_tree']

#     df = df[df['plant_type'] == plant_type] if plant_type != 'other' else df
#     df = df[df['plant_name'] == plant_name] if plant_name != 'other' else df
#     df = df[df['plant_part'] == plant_part] if plant_part != 'other' else df

#     query = set(plant_damages)

#     df['coef'] = df['plant_damage'].apply(lambda s: _jaccard_coef(s, query))
#     df = df.sort_values('coef', ascending = False).head(3)
    
#     res = [f'[Link]({r[1]["link"]}) for following plant problem: '\
#         f'type - {r[1]["plant_type"]}, name - {r[1]["plant_type"]}'\
#         f'part - {r[1]["plant_part"]}, damages - {", ".join(r[1]["plant_damage"])}' for r in df.iterrows()]

#     return res
