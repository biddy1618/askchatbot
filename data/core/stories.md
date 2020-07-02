## custom session start 0
* start
  - action_session_start_custom

## custom session start 1
* session_start_custom
  - action_session_start_custom
  
## custom session start 2
* session_start
  - action_session_start_custom
  
## hi
* intent_hi
  - action_hi

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

## garbage + no handoff
* intent_garbage_inputs
    - action_ask_handoff_to_expert
* intent_no
    - action_session_start_custom
    
## chatgoal other + handoff
* intent_chatgoal{"chatgoal_value": "__other__"}
    - action_ask_handoff_to_expert
* intent_yes
    - utter_handoff_to_a_human_expert

## chatgoal other + no handoff
* intent_chatgoal{"chatgoal_value": "__other__"}
    - action_ask_handoff_to_expert
* intent_no
    - action_session_start_custom
    
## ask handoff to expert + yes
* intent_ask_handoff_to_expert
    - action_ask_handoff_to_expert
* intent_yes
    - utter_handoff_to_a_human_expert

## ask handoff to expert + no
* intent_ask_handoff_to_expert
    - action_ask_handoff_to_expert
* intent_no
    - action_session_start_custom
    
## chatgoal explain ipm
* intent_chatgoal{"chatgoal_value": "explain_ipm"}
    - slot{"chatgoal_value": "explain_ipm"}
    - action_explain_ipm
    - action_hi
    
## chatgoal pest problem with result
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
    - form{"name": null}
    - slot{"found_result": "yes"}
    - utter_request_rating
* intent_rating
    - action_tag_rating
    
## chatgoal pest problem without result
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
    - form{"name": null}
    - slot{"found_result": "no"}
    - action_session_start_custom
    
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
    - utter_handoff_to_a_human_expert
    
## chatgoal pest problem with garbage + no handoff + continue
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
* intent_garbage_inputs
    - action_ask_handoff_to_expert
* intent_no
    - form_query_knowledge_base
    - form{"name": null}