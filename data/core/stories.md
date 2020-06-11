## hi
* intent_hi
  - action_hi
  - utter_what_is_chatgoal

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
    - utter_explain_ipm
    - utter_what_is_chatgoal
    
## chatgoal pest problem
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
    - form{"name": null}
    - utter_request_rating
* intent_rating
    - action_tag_rating
    - utter_what_is_chatgoal
    
## chatgoal do stackoverflow query
* intent_chatgoal{"chatgoal_value": "do_a_stackoverflow_query"}
    - slot{"chatgoal_value": "do_a_stackoverflow_query"}
    - form_query_stackoverflow_in_es
    - form{"name": "form_query_stackoverflow_in_es"}
    - form{"name": null}
    - utter_request_rating
* intent_rating
    - action_tag_rating
    - utter_what_is_chatgoal
    
## chatgoal goodbye
* intent_chatgoal{"chatgoal_value": "goodbye"}
    - slot{"chatgoal_value": "goodbye"}
    - utter_bye