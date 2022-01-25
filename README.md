# Introduction to Rasa

## Two parts

### NLU - understanding text (natural language understanding)

* Rule-based methods - example is regular expression, but they are not good at handling things they haven't seen before.
* Neural methods - example is transformer-based like DIET (developed at Rasa), reqiuires training data but it is flexible.
    * DIET sorts texts into intents and entitites based on examples it's been provided.
* Rasa can use both and it is recommended.

### Dialog policy - deciding what to do next

* Rule-based methods - big dialog tree of all possible paths a conversion can take.
    * Can't had digressions and are a bit of a pain to extend/maintain.
* Neural methods - transformer-based model (e.g. TED) that picks the next best turn based on the conversation so far and all the conversations it's been trained on.
    * Requires training example (the more the better), but let's users have more flexible conversations.
* At Rasa, we recommend using both approaches in tandem.

Correct any errors your assisstant made in a conversation, manually review and annotate conversations - __CONVERSATION-DRIVEN DEVELOPMENT__.

## Rasa project structuring

```
📂 /path/to/project
┣━━ 📂 actions
┃   ┣━━ 🐍 __init__.py
┃   ┗━━ 🐍 actions.py
┣━━ 📂 data   
┃   ┣━━ 📄 nlu.yml
┃   ┣━━ 📄 rules.yml
┃   ┗━━ 📄 stories.yml
┣━━ 📂 models 
┣━━ 📂 tests  
┃   ┗━━ 📄 test_stories.yml
┣━━ 📄 config.yml
┣━━ 📄 credentials.yml
┣━━ 📄 domain.yml
┗━━ 📄 endpoints.yml
```
Minimal files for Rasa:
* `config.yml`
* `domain.yml`
* Data files:
    * `nlu.yml`
    * `rules.yml`
    * `stories.yml`


# Domain file

Contains:
* Responses - utterances assistant can say.
* Intents - categories of things user can say.
* Slots - variables remembered over the course of a conversation.
* Entities - pieces of information extracted from incoming text.
* Forms and actions - add application logic & extend what your assistant can do.

# Training data and rules

* How should conversations with your chatbot go?
    - Stories - training data to teach your assistant what it should do next.
        - Memoization policy - if the story is in the training data.
        - TED policy to guess what should next action be (if not sure enough, then fallback) - pattern chatbot hasn't seen before.
    - Rules - a way to describe short pieces of conversations that always got the same way.
* How do users say things?
    - Intents
        - User checkpoints to modularize and simplify your training data, but do not overuse them.


## Couple of hints

DOs
* Use actual user converations as stories.
* Have small stoies that aren't full conversations.
* Use rules for one-off interactions (checking account balance, checking if this is a bot).
* Start with the most common intent (most people want to do the same thing).
* __Start with the smallest possible number of intents (that cover your core use case).__
    - Only start with the most popular, important intents & a way to handle things outside them.
    - Continue to build from there if that's what users need.
    - More intents - more training data, maintenance, documentation, and annotation more difficult.
    - Transformer classifiers scale linearly with the # of classes.
    - Entity extraction (with very lightweight rule-based sysems like Dickling) is often faster.
* Everything else goes in an out of scope intent.
* Each utterance should match exactly one intent in your training data.
 
DO NOTs
* Use rules for multi-turn interactions.
* Use OR statements and checkpointing often.
* Write out every possible conversation flow start to finish.
* Delay user testing!

# Entities

## Entity definition

Can be any important detail that your assistant could use later in a conversation.

## Methods

1. Using pre-built models: 
    - Duckling (numbers, urls, emails, dates).
    - SpaCy pre-built models - for extraction names, product names, locations.
2. Using RegEx: for entities that match a specific pattern.
3. ML models:
    - DIETClassifier: Lots of training data.

## Additional features

* Synonyms - mapping of the values of entity to a single entity. Synonym mapping will happen after extraction of the entities, which mean you will need some training data to enable your assistant to extract your entities.
* Lookup tables - lists of words to generate case-sensitive regular expression patterns.
* Entity role and group - allows to define the roles of the entities of the same group.
    - Roles can influence the flow of conversation, i.e. we can define different stories based on the role of extracted entities from intent and utter corresponding response.

# Slots

## Slots definition

Slots are the assistanct's (chatbot's) memory. They enable assistant to store important details and later use them in a specific context.

Slots are defined in `domain.yml` file have following fields: `type`, `influence_conversation`, `mappings: {type}`.

## Setting slots

1. Using NLU - e.g. through values of extracting entities, or using specific values if a certain intent has been predicted.
2. Using custom actions - e.g. set slots through DB API calls or other micro-services.

## Inlfuencing conversation

Slots can be used to influence the conversation, i.e. depending on the type of the slow the flow can be influenced by the value of the slot or whether the value of this slot is present. DO NOT OVERUSE THIS.

As an example, extracting transfer amount can influence the conversation, whereas checking the amount shouldn't.

## Slot mappings

1. `from_entity` - fills the slot based on the extracted entities. Parameters:
    - `role` - only applies the mapping if the extracted entity has this role.
    - `group` - ... belongs to this group.
    - `intent` - ... when this intent is predcited.
    - `not_intent` - does not apply the mapping when this intent is predicted.

2. `from_text` - will use the text of the last user messages to fill in the slot.

3. `from_intent` - fills in the slot with a specific defined value if a specific intent is predicted. Requires the specific value to be set in additional parameter `value`.

4. `from_trigger_intent` - fills a slot with a specific defined value if a __form__ is activated by a user message with a specific intent.

5. `custom` - custom slot mapping using slot validation actions. 

## Slot types

1. `text` - text can be used to store any text information, can influence the conversation based on presence (i.e. booking flight to some specific destination - setting the slot only if the "role" is "destination").

2. `boolean` - can get values `True` or `False` (i.e. check if the user is logged in or not).

3. `categorical` - stores one of the possiblN values (i.e. restaurant booking example - get a table at "medium" price restaraunt, and use that slot to make the search a little more specific).

4. `float` - store numerical value (i.e. find a restaraunt within 10 miles radius).

5. `list` - store a list of values (i.e. grocery store shopping list).

6. `any` - store any arbitrary value. It doesn't influence the conversation. Best to simply store the values that you'd like your assistant to have access to.

One can set the initial value by providing `initial_value` field in slots.

# Responses

## Buttons

Buttons have 2 fields: `title` (value of the button) and `payload` (value to send to the Rasa's server, can be intent or entity).

## Custom payload

Can get creative with payloads, i.e. one can set the date-picker for some channels (slack for instance, see more in documentation).

# NLU training pipelines and Dialog Management policies

These are configured in `config.yml` file.

## NLU pipelines

__Order in NLU pipelines matters__. High-level overview of components:

1. Tokenizers - parse user inputs into separate tokens - `WhiteSpaceTokenizer`, `SpacyTokenizer`, etc.
2. Featurizers - extract features from the tokens, turns tokens into sparse and dense vectors (one-hot encodings and embeedings) - `RegExFeaturizers`, language model featurizers, etc.
3. Classifiers - assign a label to the user's input - `DietClassifier` (does both intent classification and entity extraction).
    1. Entity extractors - extract important details - `DucklingEntityExtractor`, `DietClassifier`, etc.


## Dialogue Management policies

Training policies are techniques your assistant uses to predict on how to respond back to the user. Policy priority defines how assistant makes decisions when multiple policies predict the next action with the same accuracy.

Default policy priority in Rasa:
* 6 - RulePolicy
* 3 - MemoizationPolicy or AugmentedMemoizationPolicy
* 1 - TEDPolicy

### 2 types of policies in Rasa

1. Rule Policies - assistant makes the decision on how to respond based on rules defined inside of your `rules.yml` file.
    - `RulePolicy` - strict rule-based behaviour on the assistant. Checks the presence of story in `rules.yml`.
    - `MemoizationPolicy` - remembers the stories from `stories.yml` and tries to predict the next best action by matching the stories.
2. Machine Learning policies - assistant makes the decision on how to respond by learning from the data defined inside of the `stories.yml` file.
    - `TEDPolicy` - The Transformer Embedding Dialoague policy is a multi-task architecture for next action prediction and entity recognition.



# Custom actions

 Custom actions allow us to do a lot of stuff like making and API call or interacting with DB, and this opens up a lot of options for our assistant.

## Rasa Custom Action Example

All actions should inherit from `rasa_sdk.Action` base class. Two methods that need to be implemented:
1. `name(self) -> Text` - name given to this custom action. It is quite important since we will refer to this name in our `domain.yml`, `stories.yml`, etc.
2. `run(self, dispatcher: rasa_sdk.executor.CollectionDispatcher, tracker: rasa_sdk.Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]` - custom code to be run when this action is triggered.
    * `dispatcher` object allows you to send messages back to user.
    * `tracker` object contains relevant data that was extracted from the conversation so far (intents, entities, slot values, etc).
    * `domain` - data defined in `domain.yml` file.
    * the `run` method return list of events that should be emitted once the custom action is done, like setting the slot values - `rasa_sdk.events.SlotSet(...)`, etc.     

# Forms

Forms help up to get data from users, like before triggering some custom action the slots need to be filled, and forms come into play.

The basic scenario for trigerring form is some specific intent, then the form will be active (`active_loop`) until all the needed slots are filled, i.e. it keep asking the user for information until all the slots are filled in.

To configure the form you will need 2 rules - for activating the form, and other for deactivating.

## Validating forms

There is naming conventions for actions that validate forms - `validate_<name of the form>`. Actions for validationg custom forms are implemented using actions that inherit from `rasa_sdk.FormValidationAction` class, and implement following methods:
* `name(self) -> Text` - name of the action.
* for each slot required `validate_<slot name>(self, slot_value: Any, dispatcher: rasa_sdk.exector.CollactionDispatcher, tracker: rasa_sdk.Tracker, domain: Dict[Text, Any]) -> Dict[Text, Any]` method - the logic for filling the slots and return dictionary of slots being set (`None` if slot has not been set). 

## Wrap up

Rasa Forms autamate the process of retrieving information from the user and allow you to validate the data prgrammatically.

They won't solve everything for you though. You will still need to think about conversational design in order to keep the forms convenient for your users.

# Custom Forms

## Interruptions

* Sometimes during `active_loop` in form validation, user might utter some random intent, and in order to handle that we can introduce additional rules including that chit-chat.
* Sometimes users wants to discontinue some form validation. In this case we can introduce story that incorporates that behaviour. Like if user utters stop intent, we can call action `action_deactivate_loop` - it is default action that deactivates the active loop and resets the requested slots. In order to generalize, we need to introduce several stories with this pattern in mind.

For additional information, please, visit default actions page in Rasa documentation.

## Entities recognized only within the form

One can set up entity in a way that it can be recognized only while some active form loop by setting conditions in slots definition:
```
slots:
    pizza_size:
        type: text
        influence_conversation: true
        mappings:
        -   type: from_entity
            entity: pizza_size
            conditions:
            -   active_loop: pizza_form
                requested_slot: pizza_size
```

## Making forms dynamic

* We can introduce buttons. We can send button along with message by including buttons parameter in `utter_message` method of dispatcher.

# Integration with website

One can run `rasa run --enable-api` to be able to talk to the bot through API.

Also one can run `rasa run --enable-api --cors="*"` to configure CORS to allow all traffic to connect.

Also one can run `rasa run --enable-api --cors="*" --debug` to help debugging while intergrating with website.

# CDD and Rasa X

To install Rasa X, run the following command:
```
conda create --name rasa-x python=3.7
conda activate rasa-x
pip install --upgrade pip
pip install rasa-x --extra-index-url https://pypi.rasa.com/simple
```

One can use ngrok to share the bot with external users.

# Local set up

Install required libraries for packages to run without issues (try without these first):
```
sudo apt install pkg-config libxml2-dev libxmlsec1-dev libxmlsec1-openssl
```

Install miniconda version:
```
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod +x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh
```

Create environment for the chatbot:
```
conda --version
conda create --name askchatbot python=3.7
conda activate askchatbot
```

First set up:
```
pip install --upgrade pip
pip cache purge
pip install rasa
pip install --upgrade sanic==21.6.1
pip install ipykernel
pip install pandas
```

__BUT__ to avoid conflicts, please use `requirements.txt` file:
```
pip cache purge
pip install -r ./rasa-dev/requirements.txt
```

## Basic front end

Copy the `index.html` file and put it in the project folder from this [github repo](https://github.com/RasaHQ/how-to-rasa/tree/main/video-10-connectors). Visit the [official github page](https://github.com/scalableminds/chatroom) of the project for more details. 

Launch the server typing the following commands:
```
python -m http.server 8000
```

Make sure to run the Rasa chatbot with `--enable-api` and `--cors="*"` commands, additionally one can use `--debug` command for debugging:
```
rasa run --enable-api --cors="*" --debug --port 5005
```

## Installing Rasa X

Follow the guidelines for Rasa 1.0.x on [site](https://rasa.com/docs/rasa-x/installation-and-setup/install/rasa-ephemeral-installer/installation#quickstart).

```
curl -O https://rei.rasa.com/rei.sh && bash rei.sh -y
rasactl start --project
```

To check the status and find out the url, run the following:
```
rasactl status
```

__IMPORTANT NOTE__: Rasa X as of 04.01.2022 is not supported by Rasa 3.0.* - [source](https://rasa.com/docs/rasa-x/changelog/compatibility-matrix/). Support for [Rasa X for Rasa 3.0.*](https://forum.rasa.com/t/rasa-x-3-0/49700) is coming soon, so stay tuned for updates.

## `rasa-webchat` intergration

It is not compatible with `Rasa 3.0.*` since `rasa-webchat` requires `socket.io-client` be version of 3.1.2, but `Rasa 3.0.*` requires `python-socketio` (which `socketio` client) be later than 4.4 (and less than 6).