# The Extension Bot

Repo for the Ask Extension chatbot component demonstration.
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