# The Extension Bot

Repo for the Ask Extension chatbot component demonstration.

## Local set up and deployment

You can find the details for building the project locally in the following [`README-1-setup.md`](info/README-1-setup.md) file.

## Things you can ask the bot

The bot can:

1. Find information based on pest-related question or request.
    1. Examples of requests:
    ```
    - Something is creating tunnels on my tomato plants. When I cut them open, I see yellowish worms or larvae with red or purple areas.
    ```

    ```
    - There are tiny flies hovering all over my fruit basket. How do I get rid of them?
    ```

    ```
    - I want to release lady bugs in my garden with the goal of keeping the aphid population to a minimum. Some guidance regarding purchase and implementation of the bugs.
    ```
2. Explain `Intergrated Pest Management`.
3. Connect to expert by showing the link to reach the expert.

## Details of implementation

The bot is able to retrieve entities related to pest management like following:
1. Pest name
2. Plant name
3. Plant type
4. Plant part
5. Plant damage
6. Pest location

It uses the recognized entities to adjust the results of the search result.

Querying the data sources happens through vector-similiraties of embedded vectors of the query against the knowledge database.

* Embedding is achieving through [Universal Sentence Encoder model by Google](https://static.googleusercontent.com/media/research.google.com/en//pubs/archive/46808.pdf)
* The distance metric is [cosine similary distance](https://en.wikipedia.org/wiki/Cosine_similarity)

## Development server

The chatbot is available through `https://dev.chat.ask.eduworks.com/`.

## Front-end

[Repository](https://git.eduworks.us/ask-extension/askchatbot-widget) for the front-end.

## Rasa project structure details

```bash
📂 /path/to/project
┣━━ 📂 actions                      # actions
┃   ┣━━ 📂 static                   # static files
┃   ┃   ┣━━ 🔢 plant_matches.pkl    # data scraped from "plant diagnostic matrix"
┃   ┃   ┗━━ 🔢 plant_tree.pkl       # data scraped from "plant diagnostic matrix"
┃   ┣━━ 🐍 __init__.py              #
┃   ┣━━ 🐍 actions.py               # actions main module
┃   ┣━━ 🐍 helper.py                # helper functions for actions module
┃   ┣━━ 📄 plant_matching.ipynb     # EDA for scraped data
┃   ┗━━ 📄 requirements-action.txt  # modules used in actions module
┣━━ 📂 data                         # data for training Rasa chatbot
┃   ┣━━ 📂 lookup-tables            # lookup tables, i.e., synonyms
┃   ┃   ┣━━ 📄 plant-damage.yml     # 
┃   ┃   ┣━━ 📄 plant-disease.yml    #
┃   ┃   ┣━━ 📄 plant-name.yml       #
┃   ┃   ┣━━ 📄 plant-part.yml       #
┃   ┃   ┣━━ 📄 plant-pest.yml       #
┃   ┃   ┗━━ 📄 plant-type.yml       #
┃   ┣━━ 📄 nlu-request-plant-problem.yml    # training data for this intent
┃   ┣━━ 📄 nlu.yml                  # training data for minor intents
┃   ┣━━ 📄 rules.yml                # rule stories
┃   ┗━━ 📄 stories.yml              # general stories
┣━━ 📂 models                       # trained models
┣━━ 📂 tests                        # test folder
┃   ┗━━ 📄 test_stories.yml         # sample test
┣━━ 📄 config.yml                   # configuration file
┣━━ 📄 credentials.yml              # credentials file
┣━━ 📄 domain.yml                   # domain file
┣━━ 📄 endpoints.yml                # endpoints file
┣━━ 🐋 Dockerfile                   # dockerfile for rasa server
┣━━ 🐋 rasa-sdk.dockerfile          # dockerfile for rasa actions server
┣━━ 🐋 docker-compose.yml           # docker compose file
┣━━ 📄 index.html                   # HTML file for python web-client
┣━━ 📄 README.md                    # readme file
┣━━ 📄 endpoints.yml                # endpoints file
┗━━ 📄 requirements.txt             # requirements file
```