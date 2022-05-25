
# To Do

* Ground rules for labelling (long-term goal)

* Baseline scores with precision, recall, and misses
* Label the new data from AE
* Synonym list (layman) - initial approach using simple mapping method (lady bug. ladybug - lady beetle) before the search
* Request access to workflow from Ewald or Jasper
* For the Workflow (for running the ) and MLFlow:
    * AutoFlow
* Create the Docker file 
* Contact Jasper and Ewald on the container's access to dev's chatbot API
* True negatives in the test data - compose some samples
* Iterative improvements - to be able to show the improvements in document

* Compose the skeleton for the front-end
* Cut-off

* Focus on improvement of the metrics
* Formulate the particular problems with misses on ranking
* Include links vector comparison


# Some test questions that are failing
* The questions that are related to pests
* Another top level filter - is this pest-related
* Entity extraction - rust roses - What does rust on roses look like?
* Try changing the role composition order - basically fine-tuning
    * find the best order, and see case-by-case where it's failing (look for patterns)
* Add debugging message related to entity order

# To-do by friday

* Add scoring metrics with the new sources
* Add scoring metrics with the new entities composition logic (following order - pest, plant, damage, and remedy)

# Meeting 17.05.21

* Automate the scoring system using MLFlow - give the IP to the Jasper (done)
    * Scoring component - test different combinations of entity combinations
        * Default configuration: ['pest', 'damage', 'remedy', 'plant'] - done
        * Try these: ['pest', 'plant', 'damage', 'remedy'] - done
        * ['plant', 'pest', 'damage', 'remedy'] - done
        * ['damage', 'remedy', 'pest', 'plant'] - done
        * ['damage', 'remedy', 'plant', 'pest'] - done
        * ['pest', 'plant', 'damage'] - done
        * ['pest', 'damage', 'plant'] - done
        * ['plant', 'pest', 'damage'] - done
        * ['plant', 'damage', 'pest'] - done
        * The summary is that it doesn't make much difference in scores, I should concentrate more on the cut off and vector composition of the slots.
        * scores without the main query, only using the extracted additional queries out of the slots - done and failed
            * do the averages weighted - done (introduced new parameter ES_SLOTS_WEIGHT with value 0.3)
            * aggregate by entity roles and average the embeddings
        * Send the error queries after query change tests
        * query - `Why is my lawn getting large brown spots?`
    * Build the script to output the missing queries with all information on missing questions, automate the script (done, automate the script)
    * Take the script, refactor, remove the NA, include the NAs, compose second statitics for NAs (done)
    * Compose graph for cutoff parameter - for NA queries and valid queries
        * ES_CUT_OFF - 0.4 - done
        * ES_CUT_OFF - 0.8 - done
        * ES_CUT_OFF - 0.7 - done
        * ES_CUT_OFF - 0.6 - done
        * ES_CUT_OFF - 0.5 - done
        * ES_CUT_OFF - 0.3 - done
        * ES_CUT_OFF - 0.2 - done
        * ES_CUT_OFF - 0.1 - done
        * Send the error queries with 
    * Equivocating sentences NLP
    * Make sure that run_scoring is working (done)
* Web-component - work with Vivi on the front-end for the queries
* Computer vision - API - clear instructions on what are the objectives and integration into the Chatbot
    * Vivi will do it on her end, uploading the image and sending the request to the server
    * On my end, I should work on scoring the combinations

* Budget composition - until July included
