## configure bot
* intent_configure_bot
    - action_configure_bot
    - action_list_bot_configuration
    - action_hi
    - slot{"chatgoal_value": "None"}
    - slot{"found_result": "None"}
    
## hi
* intent_hi
    - action_configure_bot
    - action_list_bot_configuration
    - action_hi
    - slot{"chatgoal_value": "None"}
    - slot{"found_result": "None"}


## bye
* intent_bye
    - utter_bye

## thank you
* intent_thanks
    - utter_you_are_welcome

## garbage + handoff
* intent_garbage_inputs
    - action_ask_handoff_to_expert
* intent_yes
    - utter_handoff_to_a_human_expert
    - utter_bye

## garbage + no handoff
* intent_garbage_inputs
    - action_ask_handoff_to_expert
* intent_no
    - utter_bye
    
## chatgoal other + handoff
* intent_chatgoal{"chatgoal_value": "__other__"}
    - action_ask_handoff_to_expert
* intent_yes
    - utter_handoff_to_a_human_expert
    - utter_bye

## chatgoal other + no handoff
* intent_chatgoal{"chatgoal_value": "__other__"}
    - action_ask_handoff_to_expert
* intent_no
    - utter_bye
    
## ask handoff to expert + yes
* intent_ask_handoff_to_expert
    - action_ask_handoff_to_expert
* intent_yes
    - utter_handoff_to_a_human_expert
    - utter_bye

## ask handoff to expert + no
* intent_ask_handoff_to_expert
    - action_ask_handoff_to_expert
* intent_no
    - utter_bye
    
## chatgoal explain ipm
* intent_chatgoal{"chatgoal_value": "explain_ipm"}
    - slot{"chatgoal_value": "explain_ipm"}
    - action_explain_ipm
    - action_hi
    - slot{"chatgoal_value": "None"}
    - slot{"found_result": "None"}
    
## chatgoal pest problem, with result
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
    - form{"name": null}
    - slot{"hits_summaries": []}
    - action_present_hits
    - slot{"found_result": "yes"}
    - utter_request_rating
* intent_inform
    - utter_thanks
    - utter_bye
    
## chatgoal pest problem, without result + handoff
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
    - form{"name": null}
    - slot{"hits_summaries": []}
    - action_present_hits
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_yes
    - utter_handoff_to_a_human_expert
    - utter_bye
    
## chatgoal pest problem, without result + no handoff
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
    - form{"name": null}
    - slot{"hits_summaries": []}
    - action_present_hits
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_no
    - utter_bye
    
## chatgoal pest problem, with bot configuration, with result
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_configure_bot
    - action_configure_bot
    - action_list_bot_configuration
    - form_query_knowledge_base
    - form{"name": null}
    - slot{"hits_summaries": []}
    - action_present_hits
    - slot{"found_result": "yes"}
    - utter_request_rating
* intent_inform
    - utter_thanks
    - utter_bye
    
## chatgoal pest problem, with bot configuration, without result + handoff
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_configure_bot
    - action_configure_bot
    - action_list_bot_configuration
    - form_query_knowledge_base
    - form{"name": null}
    - slot{"hits_summaries": []}
    - action_present_hits
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_yes
    - utter_handoff_to_a_human_expert
    - utter_bye
    
## chatgoal pest problem, with bot configuration,  without result + no handoff
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_configure_bot
    - action_configure_bot
    - action_list_bot_configuration
    - form_query_knowledge_base
    - form{"name": null}
    - slot{"hits_summaries": []}
    - action_present_hits
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_no
    - utter_bye
    
## chatgoal pest problem with garbage + handoff
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_garbage_inputs
    - action_ask_handoff_to_expert
* intent_yes
    - action_deactivate_form
    - form{"name": null}
    - slot{"hits_summaries": []}
    - utter_handoff_to_a_human_expert
    - utter_bye
    
## chatgoal pest problem with garbage + no handoff + continue, with results
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_garbage_inputs
    - action_ask_handoff_to_expert
* intent_no
    - form_query_knowledge_base
    - form{"name": null}
    - slot{"hits_summaries": []}
    - action_present_hits
    - slot{"found_result": "yes"}
    - utter_request_rating
* intent_inform
    - utter_thanks
    - utter_bye
    
## chatgoal pest problem with garbage + no handoff + continue, without result + handoff
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_garbage_inputs
    - action_ask_handoff_to_expert
* intent_no
    - form_query_knowledge_base
    - form{"name": null}
    - slot{"hits_summaries": []}
    - action_present_hits
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_yes
    - utter_handoff_to_a_human_expert
    - utter_bye
    
## chatgoal pest problem with garbage + no handoff + continue, without result + no handoff
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_garbage_inputs
    - action_ask_handoff_to_expert
* intent_no
    - form_query_knowledge_base
    - form{"name": null}
    - slot{"hits_summaries": []}
    - action_present_hits
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_no
    - utter_bye
    