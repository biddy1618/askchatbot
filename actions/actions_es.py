from re import A
from typing import Dict, Text, Any, List, Union, Optional

import pandas as pd

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

from actions import helper
    
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
        last_intent = tracker.active_form.get("trigger_message", {})\
            .get("intent", {}).get("name", 'intent_help_question')

        if last_intent == 'intent_help_pest':
            if tracker.get_slot('pest_causes_damage') == 'no':
                updated_slots.remove('pest_damage_description')
        else: 
            updated_slots.remove('pest_causes_damage')
            updated_slots.remove('pest_damage_description')

        logger.info(f'validate_es_query_form - required slots - {updated_slots}')
        logger.info(f'validate_es_query_form - required slots - END')

        return updated_slots

class ActionSubmitESQueryForm(Action):
    '''Custom action for submitting form - action_submit_es_query_form.'''
    
    def name(self) -> Text:
        return 'action_submit_es_query_form'
    

    def _create_text_for_pest(
        self,
        index   : int, 
        hit     : dict, 
        score   : float, 
        header  : str
        ) -> str:
        '''Prepares a message for the user.'''
        
        name        = hit["_source"]["name"]
        ask_title   = hit["_source"]["ask_title"]
        pn_url      = hit["_source"]["urlPestNote"]
        qt_url      = hit["_source"]["urlQuickTipPestNote"]
        pdi_url     = hit["_source"]["urlPestDiseaseItems"]
        tp_url      = hit["_source"]["urlTurfPests"]
        wi_url      = hit["_source"]["urlWeedItems"]
        ep_url      = hit["_source"]["urlExoticPests"]
        ask_url     = hit["_source"]["ask_url"]
        
        '''
        BE VERY CAREFUL:
        \n\n does not work. It does not wrap the sentences
        

        list symbol
        Do not use:
        "-", " >", "\t", "+"
        s = " o"  # this works, but not so nice
        s = r"\-"

        divider line
        Do not use:
        divider = "======================================"
        divider = "\  \n"
        divider = r"\-"  # OK
        '''

        divider_long = (
            r"\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-"
            r"\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-"
        )

        text = ""
        if index == 0:
            text = f'{divider_long}\n{header}\n'

        if ask_url:
            if not ask_title:
                ask_title = 'askextension'

            text = f'{text}({score:.2f})**[{ask_title}]({ask_url})**\n'

        else:
            if not name:
                name = 'ipm'

            # just pick one ipm url, with pest notes the most important one
            ipm_url = ""

            '''
            Order of importance (lower - more important):
            
            urlTurfPests
            urlWeedItems
            urlExoticPests
            urlQuickTipPestNote
            urlPestDiseaseItems
            urlPestNote
            '''

            if tp_url:
                ipm_url = tp_url
            if wi_url:
                ipm_url = wi_url
            if ep_url:
                ipm_url = ep_url
            if qt_url:
                ipm_url = qt_url
            if pdi_url:
                ipm_url = pdi_url
            if pn_url:
                ipm_url = pn_url

            # video_link = None
            # if hit["best_video"]:
            #     video_title = hit["best_video"]["videoTitle"]
            #     video_link = hit["best_video"]["videoLink"]

            text = f"{text}({score:.2f})**[{name}]({ipm_url})**\n"
            # if video_link:
            #     text = f"{text}{s} _[video: '{video_title}']({video_link})_\n"

        return text

    def summarize_hits(
        self,    
        hits_ask: dict, 
        hits_ipm: dict
        ) -> list:
        '''Create a list of dictionaries, where each dictionary contains those items we
        want to use when presenting the hits in a conversational manner to the user.'''
        
        pests_summaries = []
        
        if not hits_ask and not hits_ipm:
            return pests_summaries

        for index, hit in enumerate(hits_ask[: min(3, len(hits_ask))]):
            hit_summary = {}
            score = hit["_score_max"]
            hit_summary["message"] = self._create_text_for_pest(
                index, hit, score, "From askextension data:"
            )
            pests_summaries.append(hit_summary)

        for index, hit in enumerate(hits_ipm[: min(3, len(hits_ipm))]):
            hit_summary = {}
            score = hit["_score_weighted"]
            hit_summary["message"] = self._create_text_for_pest(
                index, hit, score, "From IPM data:"
            )
            pests_summaries.append(hit_summary)

        return pests_summaries
    
    async def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any],
    ) -> List[Dict]:
        '''Define what the form has to do after all required slots are filled.'''

        problem_description         = tracker.get_slot('problem_description')
        pest_causes_damage          = tracker.get_slot('pest_causes_damage')
        pest_damage_description     = None
        
        if pest_causes_damage != "no":
            pest_damage_description = tracker.get_slot('pest_damage_description')
        
        
        if not config.es_imitate:
            results = await submit(
                problem_description,
                pest_damage_description
            )

            buttons = [
                {'title': 'Start over',                 'payload': '/intent_greet'},
                {'title': 'Connect me to expert',   'payload': '/intent_request_expert'}
            ]

            
            dispatcher.utter_message(text = results, buttons = buttons)
            # logger.info('ASK results')
            # logger.info(json.dumps(hits_ask, indent = 4))
            # logger.info('IPM results')
            # logger.info(json.dumps(hits_ipm, indent = 4))
        else:
            message = "Not doing an actual elastic search query."
            dispatcher.utter_message(message)
            hits_ask = []
            hits_ipm = []

        return []