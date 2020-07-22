## configure bot
* intent_configure_bot
    - action_configure_bot
    - action_list_bot_configuration
    - action_hi
    - slot{"found_result": "None"}
    
## hi
* intent_hi
    - action_configure_bot
    - action_list_bot_configuration
    - action_hi
    - slot{"found_result": "None"}

## bye
* intent_bye
    - utter_bye

## thank you
* intent_thanks
    - utter_you_are_welcome

## you are confused + lets start over + yes
* intent_you_are_confused
    - utter_lets_start_over
* intent_yes
    - action_list_bot_configuration
    - action_hi
    - slot{"found_result": "None"}

## you are confused + lets start over + no
* intent_you_are_confused
    - utter_lets_start_over
* intent_no
    - utter_bye
    
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
    
## out of scope, + handoff
* intent_out_of_scope
    - action_ask_handoff_to_expert
* intent_yes
    - utter_handoff_to_a_human_expert
    - utter_bye

## out of scope, + no handoff
* intent_out_of_scope
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
    
## explain ipm
* intent_explain_ipm
    - action_explain_ipm
    - action_hi
    - slot{"found_result": "None"}
    
## i have a pest, with result
* intent_i_have_a_pest
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
    - form{"name": null}
    - form_present_hits
    - form{"name": "form_present_hits"}
    - form{"name": null}
    - slot{"found_result": "yes"}
    - utter_great
    - utter_bye
    
## i have a pest, without result + handoff
* intent_i_have_a_pest
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
    - form{"name": null}
    - form_present_hits
    - form{"name": "form_present_hits"}
    - form{"name": null}
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_yes
    - utter_handoff_to_a_human_expert
    - utter_bye
    
## i have a pest, without result + no handoff + no other pest problem
* intent_i_have_a_pest
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
    - form{"name": null}
    - form_present_hits
    - form{"name": "form_present_hits"}
    - form{"name": null}
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_no
    - utter_another_pest_problem_i_can_help_with
* intent_no
    - utter_bye
    
## i have a pest, without result + no handoff + other pest problem
* intent_i_have_a_pest
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
    - form{"name": null}
    - form_present_hits
    - form{"name": "form_present_hits"}
    - form{"name": null}
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_no
    - utter_another_pest_problem_i_can_help_with
* intent_yes
    - action_kickoff_intent_i_have_a_pest
    
## i have a pest, with bot configuration, with result
* intent_i_have_a_pest
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_configure_bot
    - action_configure_bot
    - action_list_bot_configuration
    - form_query_knowledge_base
    - form{"name": null}
    - form_present_hits
    - form{"name": "form_present_hits"}
    - form{"name": null}
    - slot{"found_result": "yes"}
    - utter_great
    - utter_bye
    
## i have a pest, with bot configuration, without result + handoff
* intent_i_have_a_pest
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_configure_bot
    - action_configure_bot
    - action_list_bot_configuration
    - form_query_knowledge_base
    - form{"name": null}
    - form_present_hits
    - form{"name": "form_present_hits"}
    - form{"name": null}
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_yes
    - utter_handoff_to_a_human_expert
    - utter_bye
    
## i have a pest, with bot configuration,  without result + no handoff + no other pest
* intent_i_have_a_pest
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_configure_bot
    - action_configure_bot
    - action_list_bot_configuration
    - form_query_knowledge_base
    - form{"name": null}
    - form_present_hits
    - form{"name": "form_present_hits"}
    - form{"name": null}
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_no
    - utter_another_pest_problem_i_can_help_with
* intent_no
    - utter_bye
    
## i have a pest, with bot configuration,  without result + no handoff + another pest
* intent_i_have_a_pest
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_configure_bot
    - action_configure_bot
    - action_list_bot_configuration
    - form_query_knowledge_base
    - form{"name": null}
    - form_present_hits
    - form{"name": "form_present_hits"}
    - form{"name": null}
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_no
    - utter_another_pest_problem_i_can_help_with
* intent_yes
    - action_kickoff_intent_i_have_a_pest
    
    
## i have a pest,with garbage + handoff
* intent_i_have_a_pest
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_garbage_inputs
    - action_ask_handoff_to_expert
* intent_yes
    - action_deactivate_form
    - form{"name": null}
    - utter_handoff_to_a_human_expert
    - utter_bye
    
## i have a pest,with garbage + no handoff + continue, with results
* intent_i_have_a_pest
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_garbage_inputs
    - action_ask_handoff_to_expert
* intent_no
    - form_query_knowledge_base
    - form{"name": null}
    - form_present_hits
    - form{"name": "form_present_hits"}
    - form{"name": null}
    - slot{"found_result": "yes"}
    - utter_great
    - utter_bye
    
## i have a pest,with garbage + no handoff + continue, without result + handoff
* intent_i_have_a_pest
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_garbage_inputs
    - action_ask_handoff_to_expert
* intent_no
    - form_query_knowledge_base
    - form{"name": null}
    - form_present_hits
    - form{"name": "form_present_hits"}
    - form{"name": null}
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_yes
    - utter_handoff_to_a_human_expert
    - utter_bye
    
## i have a pest,with garbage + no handoff + continue, without result + no handoff + no other pest
* intent_i_have_a_pest
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_garbage_inputs
    - action_ask_handoff_to_expert
* intent_no
    - form_query_knowledge_base
    - form{"name": null}
    - form_present_hits
    - form{"name": "form_present_hits"}
    - form{"name": null}
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_no
    - utter_another_pest_problem_i_can_help_with
* intent_no
    - utter_bye

## i have a pest,with garbage + no handoff + continue, without result + no handoff + another pest
* intent_i_have_a_pest
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_garbage_inputs
    - action_ask_handoff_to_expert
* intent_no
    - form_query_knowledge_base
    - form{"name": null}
    - form_present_hits
    - form{"name": "form_present_hits"}
    - form{"name": null}
    - slot{"found_result": "no"}
    - action_ask_handoff_to_expert
* intent_no
    - utter_another_pest_problem_i_can_help_with
* intent_yes
    - action_kickoff_intent_i_have_a_pest