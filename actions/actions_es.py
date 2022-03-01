from re import A
from typing import Dict, Text, Any, List, Union

import pandas as pd

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.events import (
    SlotSet,
    EventType
)

from actions.es import config
from actions.es.es import submit

import logging
logger = logging.getLogger(__name__)

import inflect
inflecter = inflect.engine()

PEST_NAME_MUST_BE_SINGULAR      = ['mildew']
TARGET_NAME_MUST_BE_SINGULAR    = ['house', 'kitchen', 'basement', 'lawn']

from actions import helper

class ActionKickoffAnotherIHaveAPestIntent(Action):
    '''Kickoff another intent_i_have_a_pest, after cleaning out the Tracker.'''

    def name(self) -> Text:
        return "action_kickoff_intent_i_have_a_pest"

    async def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:
        
        events = helper._reset_slots()
        events.extend(helper._next_intent("intent_i_have_a_pest"))
        
        return events


class ActionKickoffAnotherIHaveAQuestionIntent(Action):
    '''Kickoff another intent_i_have_a_question, after cleaning out the Tracker.'''

    def name(self) -> Text:
        return 'action_kickoff_intent_i_have_a_question'

    async def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:
        
        events = helper._reset_slots()
        events.extend(helper._next_intent('intent_i_have_a_question'))
        
        return events



class ActionAskHandoffToExpert(Action):
    '''Asks if user wants to ask the question to an expert/human.'''

    def name(self) -> Text:
        return 'action_ask_handoff_to_expert'

    async def run(
        self,
        dispatcher  : CollectingDispatcher,
        tracker     : Tracker,
        domain      : Dict[Text, Any]
        ) -> List[EventType]:

        dispatcher.utter_message(template = 'utter_ask_connect_expert')
    

# class ValidateQueryKnowledgeBaseForm(FormValidationAction):
#     '''Query the Knowledge Base.'''

#     def name(self) -> Text:
#         return 'validate_query_knowledge_base_form'


    # async def required_slots(
    #     self,
    #     domain_slots: List[Text],
    #     dispatcher  : CollectingDispatcher,
    #     tracker : Tracker,
    #     domain: Dict[Text, Any],
    #     ) -> List[Text]:
    #     '''A list of required slots that the form has to fill.'''

    #     def how_did_we_get_here(tracker: Tracker) -> Text:
    #         '''Find out if we came here because of a question or a pest problem.
    #         Do this by looking at all the events, and find the latest one that could have
    #         triggered the calling of this form.'''
            
    #         df = pd.DataFrame(tracker.events)
    #         loc_pest        = 0
    #         loc_question    = 0
    #         if '/intent_i_have_a_pest'      in df['text'].values:
    #             loc_pest        = df[df['text'] == '/intent_i_have_a_pest'      ].index.values[-1]
    #         if '/intent_i_have_a_question'  in df['text'].values:
    #             loc_question    = df[df['text'] == '/intent_i_have_a_question'  ].index.values[-1]

    #         if loc_pest > loc_question:
    #             return '/intent_i_have_a_pest'

    #         return '/intent_i_have_a_question'

    #     slots = []

    #     if how_did_we_get_here(tracker) == '/intent_i_have_a_pest':
    #         slots = ['pest_problem_description']
    #         if tracker.get_slot('pest_causes_damage') != 'no':
    #             slots.extend(['pest_causes_damage', 'pest_damage_description'])
        
    #     else: slots = ['question']

    #     return slots


    # def slot_mappings(self) -> Dict[Text, Union[Dict, List[Dict]]]:
    #     '''A dictionary to map required slots to
    #         - an extracted entity
    #         - intent: value pairs
    #         - a whole message
    #         or a list of them, where a first match will be picked.'''

    #     return {
    #         "question": [
    #             self.from_text(
    #                 not_intent=["intent_garbage_inputs", "intent_configure_bot"]
    #             )
    #         ],
    #         "pest_problem_description": [
    #             self.from_text(
    #                 not_intent=["intent_garbage_inputs", "intent_configure_bot"]
    #             )
    #         ],
    #         "pest_causes_damage": [
    #             self.from_intent(value="yes", intent="intent_yes"),
    #             self.from_intent(value="no" , intent="intent_no"),
    #         ],
    #         "pest_damage_description": [
    #             self.from_text(
    #                 not_intent=["intent_garbage_inputs", "intent_configure_bot"]
    #             )
    #         ],
    #     }


    # def pest_name_plural(self, pest_name: str) -> str:
    #     '''Returns the pest_name in plural form.'''
        
    #     pest_singular = inflecter.singular_noun(pest_name)
    #     if not pest_singular: pest_singular = pest_name
        
    #     pest_plural = inflecter.plural_noun(pest_singular)
        
    #     return pest_plural


    # def keep_pest_name_singular(self,name: str) -> str:
    #     '''Returns True if the pest name only makes sense in singular form.'''
        
    #     name_lower = name.lower()
        
    #     for key in PEST_NAME_MUST_BE_SINGULAR:
    #         if key in name_lower:
    #             return True
        
    #     return False
    

    # def validate_pest_problem_description(
    #     self,
    #     value       : Text,
    #     dispatcher  : CollectingDispatcher,
    #     tracker     : Tracker,
    #     domain      : Dict[Text, Any],
    #     ) -> Dict[Text, Any]:
    #     '''Once pest problem is described:

    #     If no pest name was extracted:
    #       -> do not ask for damage
    #       -> set the damage equal to the description

    #     If a pest name was extracted:
    #       -> build damage question to ask, using the pest name in plural form
    #     '''

    #     # see if a pest name was extracted from the problem description
    #     pest_name   = tracker.get_slot('pest_name')

    #     # see if a target name was extracted from the problem description
    #     target_name = tracker.get_slot('target_name')

    #     if not pest_name:
    #         # question = "Is there any damage?"
    #         return {
    #             'pest_problem_description'  : value,
    #             'pest_causes_damage'        : 'did-not-ask',
    #             'pest_damage_description'   : value,
    #         }

    #     if self.keep_pest_name_singular(pest_name):
    #         if target_name:
    #             question = (
    #                 f'Is the {pest_name.lower()} causing any damage to the '
    #                 f'{target_name.lower()}?'
    #             )
    #         else:
    #             question = f'Is the {pest_name.lower()} causing any damage?'
    #         return {
    #             'pest_problem_description'  : value,
    #             'cause_damage_question' : question,
    #         }

    #     pest_plural = self.pest_name_plural(pest_name)
    #     if target_name:
    #         question = (
    #             f"Are the {pest_plural.lower()} causing any damage to the "
    #             f"{target_name.lower()}?"
    #         )
    #     else:
    #         question = f"Are the {pest_plural.lower()} causing any damage?"
    #     return {"pest_problem_description": value, "cause_damage_question": question}
    
class ActionSubmitQueryKnowledgeBaseForm(Action):
    '''Custom action for submitting form - query_knowledge_base_form.'''
    
    def name(self) -> Text:
        return 'action_submit_query_knowledge_base_form'
    

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

        pest_name                   = tracker.get_slot('question')
        pest_problem_description    = tracker.get_slot('pest_problem_description')
        pest_causes_damage          = tracker.get_slot('pest_causes_damage')
        # pest_damage_description     = None
        
        # if pest_causes_damage != "no":
        pest_damage_description = tracker.get_slot('pest_damage_description')
        
        question = tracker.get_slot('question')

        if not config.imitate:
            hits_ask, hits_ipm = await submit(
                question,
                pest_name,
                pest_problem_description,
                pest_damage_description
            )
        else:
            message = "Not doing an actual elastic search query."
            dispatcher.utter_message(message)
            hits_ask = []
            hits_ipm = []

        pests_summaries = self.summarize_hits(hits_ask, hits_ipm)
        return [SlotSet("pests_summaries", pests_summaries)]