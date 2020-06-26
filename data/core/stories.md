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

## chatgoal other
* intent_chatgoal{"chatgoal_value": "__other__"}
    - utter_canthelp
    - utter_please_askexpert
    
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
    
