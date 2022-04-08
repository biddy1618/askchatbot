from typing import Dict, Text, Any, List, Tuple

import pandas as pd

from rasa_sdk import Tracker
from rasa_sdk.events import (
    SlotSet,
    ActionExecuted,
    UserUttered
)

PATH_STATIC = './actions/static/'

import logging
logger = logging.getLogger(__name__)

logger.info('----------------------------------------------')
logger.info('Rasa Actions Server')
logger.info('- loading static files')
db = None
try:
    plant_tree      = pd.read_pickle(PATH_STATIC + 'plant_tree.pkl')
    plant_matches   = pd.read_pickle(PATH_STATIC + 'plant_matches.pkl')
    db = {
        'plant_tree'    : plant_tree,
        'plant_matches' : plant_matches
    }
    logger.info('- success')
except:
    logger.error('  error loading static files')
logger.info('----------------------------------------------')

params = {
    'es_search_size': int,
    'es_top_n'      : int,
    'es_cut_off'    : float,
    'es_ask_weight' : float
}

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
    'debug_slots'       : 'Extracted slots:</br>',
    'debug_no_results'  : 'Unfortunately, could not find any results that might help you... Try reducing <strong>es_cut_off</strong> parameter.',
    'debug_results'     : 'Top {0} results.',
    'debug_slot_results': 'Results with slots improvement... Top {0} results.',
    'debug_no_es'       : 'Not doing an actual elastic search query.',
}

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


def _get_plant_names(
    plant_type      : Text          = 'other',
    n               : int           = 10) -> List[Text]:
    '''Get plant names corresponding to plant type.'''

    df = db['plant_matches']
    df = df[df['plant_type'] == plant_type] if plant_type != 'other' else df
    
    pn = df['plant_name'].drop_duplicates()
    if pn.shape[0] > n:
        pn = pn.sample(n)
    
    return pn.tolist()


def _get_plant_parts(
    plant_type      : Text          = 'other',
    plant_name      : Text          = 'other',
    n               : int           = 10) -> List[Text]:
    '''Get plant details corresponding to plant descriptions.'''

    pp = None
    df = db['plant_matches']
    df = df[df['plant_type'] == plant_type] if plant_type != 'other' else df
    df = df[df['plant_name'] == plant_name] if plant_name != 'other' else df
    
    pp = df['plant_part'].drop_duplicates()
    if pp.shape[0] > n:
        pp = pp.sample(n)

    return pp.tolist()


def _get_plant_damages(
    plant_type      : Text          = 'other',
    plant_name      : Text          = 'other',
    plant_part      : Text          = 'other',
    n               : int           = 10) -> List[Text]:
    '''Get plant details corresponding to plant descriptions.'''

    pd = []
    df = db['plant_matches']
    df = df[df['plant_type'] == plant_type] if plant_type != 'other' else df
    df = df[df['plant_name'] == plant_name] if plant_name != 'other' else df
    df = df[df['plant_part'] == plant_part] if plant_part != 'other' else df
    
    pd = df['plant_damage'].drop_duplicates()
    if pd.shape[0] > n:
        pd = pd.sample(10)
    
    return pd.tolist()


def _jaccard_coef(s1: set, s2: set) -> float:  
    return len(s1.intersection(s2)) / len(s1.union(s2))


def _get_problem_links(
    plant_type      : Text = 'other',
    plant_name      : Text = 'other',
    plant_part      : Text = 'other',
    plant_damages   : List[Text] = []) -> List[Text]:
    '''Get information associated with plant problem descriptions.'''

    df = db['plant_tree']

    df = df[df['plant_type'] == plant_type] if plant_type != 'other' else df
    df = df[df['plant_name'] == plant_name] if plant_name != 'other' else df
    df = df[df['plant_part'] == plant_part] if plant_part != 'other' else df

    query = set(plant_damages)

    df['coef'] = df['plant_damage'].apply(lambda s: _jaccard_coef(s, query))
    df = df.sort_values('coef', ascending = False).head(3)
    
    res = [f'[Link]({r[1]["link"]}) for following plant problem: '\
        f'type - {r[1]["plant_type"]}, name - {r[1]["plant_type"]}'\
        f'part - {r[1]["plant_part"]}, damages - {", ".join(r[1]["plant_damage"])}' for r in df.iterrows()]

    return res


def _parse_config_message(text: str) -> Tuple[str, str]:
    parameter, value = None, None
    try:
        _, parameter, value = [t.strip() for t in text.split(' ')]
        if parameter in params  : value = params[parameter](value)
        else                    : raise Exception  
    except Exception:
        parameter, value = None, None
    return parameter, value


def _get_config_message(config):
    
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
