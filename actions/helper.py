from typing import Dict, Text, Any, List, Tuple

import pandas as pd
from difflib import get_close_matches

from rasa_sdk import Tracker
from rasa_sdk.events import (
    SlotSet,
)


PATH_STATIC = './actions/static/'

import logging
logger = logging.getLogger(__name__)

logger.info('----------------------------------------------')
logger.info('Rasa Actions Server')
logger.info('- loading static files')
db = None
try:
    plant_df        = pd.read_pickle(PATH_STATIC + 'plant_tree.pkl')
    plant_matches   = pd.read_pickle(PATH_STATIC + 'plant_matches.pkl')
    db = {
        'plant_df'      : plant_df,
        'plant_matches' : plant_matches
    }
    logger.info('  success')
except:
    logger.error('  error loading static files')
logger.info('----------------------------------------------')
    

def _reset_slots(tracker: Tracker) -> List[Any]:
    """Clean up slots from all previous forms"""
    
    events = []

    for k, v in tracker.slots.items():
        if k in ['shown_greeting', 'shown_privacy_policy']: 
            events.append(SlotSet(k, True))
        elif k == 'shown_explain_ipm':
            events.append(SlotSet(k, v))
        else: 
            events.append(SlotSet(k, None))

    return events

def _get_plant_names(
    plant_type      : Text          = 'other',
    n               : int           = 10) -> List[Text]:
    """Get plant names corresponding to plant type"""

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
    """Get plant details corresponding to plant descriptions"""

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
    """Get plant details corresponding to plant descriptions"""

    pd = []
    df = db['plant_matches']
    df = df[df['plant_type'] == plant_type] if plant_type != 'other' else df
    df = df[df['plant_name'] == plant_name] if plant_name != 'other' else df
    df = df[df['plant_part'] == plant_part] if plant_part != 'other' else df
    
    pd = df['plant_damage'].drop_duplicates()
    if pd.shape[0] > n:
        pd = pd.sample(10)
    
    return pd.tolist()