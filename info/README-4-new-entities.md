# New entities mapping logic

## New entities

Entities:
* action
* descr
* location
* name
* part (can have only plant and pest as a role)
* type (can have only plant and pest as a role)

Roles:
* pest
* plant
* damage
* remedy


Groups:
* from 1 to n

## Basic ground rules and guidelines

* Label compound composite names of pests and plants as a single entity
    * peach leaf curl
    * oriental cockroaches
    * roof rats
    * rat poison
    * carpet beetle
    * blossom end rot
    * fungus gnats
    * gopher trap
    * ground squirrels
    * head lice
    * weed killer
* Distinguish between verb and adjectives, specifically label verbs as verb explicitly (since POS of modifier as adjective of the verb is still VERB)
    * Dying man - VERB NOUN (mark __dying__ as ACTION)
    * Answering machine - VERB NOUN (mark __answering__ as ACTION)
    * Heating element - NOUN NOUN (mark __heating__ as ACTION)
    * Landing field - NOUN NOUN (mark __landing__ as ACTION)
    * leaves are covered - NOUN AUX VERB (mark __covered__ as ACTION)


## Mapping logic

Order:
1. Groups
2. Roles
    1. Pest
    2. Damage
    3. Remedy
    4. Plant
3. Entities:
    1. descr
    2. (type |) name (| part)
    3. action
    4. location

## Slot strucure

```JavaScript
{
    // Group keys
    Group1:
    {
        // Role keys with ordered tuples of entities
        pest    : [(order, entity_name, entity_value), ...],
        damage  : [(order, entity_name, entity_value), ...],
        remedy  : [(order, entity_name, entity_value), ...],
        plant   : [(order, entity_name, entity_value), ...]
    },
    ...,
    GroupN: ...
}
```


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
* My peonies are not growing well
* My peony is not growing well
* The questions that are related to pests
* Another top level filter - is this pest-related
* Entity extraction - rust roses - What does rust on roses look like?
* Try changing the role composition order - basically fine-tuning
    * find the best order, and see case-by-case where it's failing (look for patterns)
* Add debugging message related to entity order
* Add