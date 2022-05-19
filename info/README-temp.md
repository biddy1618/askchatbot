
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
    * Build the script to output the missing queries with all information on missing questions (done, automate the script)
    * Take the script, regenerate, remove the NA, include the NAs, compose second statitics for NAs
    * Compose graph for cutoff parameter - for NA queries and valid queries
    * Equivocating sentences NLP
    * Make sure that run_scoring is working.
* Web-component - work with Vivi on the front-end for the queries
* Computer vision - API - clear instructions on what are the objectives and integration into the Chatbot


* Budget composition - until July included