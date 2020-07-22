"""
nlu-askextension-tomato-california.md
=====================================
## intent: askextension_tomato_california/<name_of_intent>
- <question>

name_of_intent: <faq_id>_<state>_<title>
(-) all lowercase
(-) strip off '#id' from the end
(-) replace unicode with ' ':
    (-) \u00a0
(-) replace escapes:
    (-) \n -> ' '
    (-) \" -> '
(-) replace '&' by 'and'
(-) replace nonalphanumeric by space:
    (-) ? ! . , ; : - [ ] { } ( ) ' " * -> ' '
(-) single space
(-) replace space by '_'

question: <question>
(-) replace unicode with ' ' (see intent)
(-) replace escapes (see intent)
(-) single space
(-) separate out & mark up urls:
    (-) [name.pdf](http...../name.pdf)   [.pdf]
    (-) [name.php](http...../name.php)   [.php, .php/]
    (-) [name.html](http..../name.html)  [.html]

--
responses-askextension-tomato-california.md
===========================================
## name_of_intent
* askextension_tomato_california/name_of_intent
    - <response>

<response>    
(-) replace unicode with ' ' (see intent)
(-) replace escapes (see intent)
(-) single space
(-) separate out & mark up urls (see question)

--
instruct-and-track.csv
======================
A table to instruct the generator

faq-id, skip, selector

with:
(-) faq-id
(-) skip     : [True/False] - do not include this one
(-) selector : name of the selector that includes it
"""
