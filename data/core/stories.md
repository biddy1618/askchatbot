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
    
## chatgoal explain ipm + pest problem
* intent_chatgoal{"chatgoal_value": "explain_ipm"}
    - slot{"chatgoal_value": "explain_ipm"}
    - utter_explain_ipm
    - utter_do_you_have_a_pest_problem
* intent_yes
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
    - form{"name": null}
    
    
## chatgoal explain ipm + no pest problem
* intent_chatgoal{"chatgoal_value": "explain_ipm"}
    - slot{"chatgoal_value": "explain_ipm"}
    - utter_explain_ipm
    - utter_do_you_have_a_pest_problem
* intent_no
    - utter_to_be_implemented_2
    
## chatgoal pest problem
* intent_chatgoal{"chatgoal_value": "I_have_a_pest"}
    - slot{"chatgoal_value": "I_have_a_pest"}
    - form_query_knowledge_base
    - form{"name": "form_query_knowledge_base"}
    - form{"name": null}