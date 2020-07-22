"""
nlu-askextension-tomato-california.md
=====================================
## intent: askextension_tomato_california/<faq_id>_<state>
- <title> <question>

<title>:
(-) all lowercase
(-) strip off '#id' from the end
(-) add a '.' if it does not yet end with a proper punctuation: 
    ? ! . , ; :

<title> <question>
(-) replace unicode with ' ':
    (-) \u00a0
(-) replace escapes:
    (-) \n -> ' '
    (-) \" -> '
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
