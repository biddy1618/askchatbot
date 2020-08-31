# The Extension Bot

Repo for the Ask Extension chatbot component demonstration completed in the 2019-2020 funding cycle.

## Things you can ask the bot

The bot can:
1. Find  information based on an open question, for example:

   ```bash
   - when I import a christmas tree from Michigan to california, is there a tax I need to pay?
   ```

   ```bash
   - Should I desprout potatoes when I store them in the winter?
   ```

   ```bash
   - I have ants in my kitchen and want to know how to get rid of them
   ```

   ```bash
   - I think I have lanternflies
   ```

   ```bash
   - My tomatoes have black spots, any idea what it could be?
   ```

   

2. Find information based on a `pest problem description` & an optional `damage description`, for example:

   ```bash
   - pest problem description: I have ants in the house 
   -       damage description: They create holes in my wall
   ```

   ```bash
   - pest problem description: There are a lot of bees in my back yard
   -       damage description: They burrow into the wood piles
   ```

   ```bash
   - pest problem description: I got grubs in my lawn 
   -       damage description: The grass is completely dead in certain spots
   ```

   

3. If the chatbot cannot find anything, or if the user indicates that the provided information is not helpful, the bot will ask the user if they would like to ask an expert. If yes, a link will be provided where the user can ask their question to an expert.

4. Explain `Integrated Pest Management (IPM)`



## Hardware requirements

The bot was developed & deployed on an EC2 of **c5.2xlarge**:

- 8 vCPU
- 16 Gb RAM   (Recommended to increase to 32 Gb)
- 100 Gb disk  (Recommended to increase to 200 Gb)

## Data sources

The bot uses data that was scraped from these websites:

- [ipm data](http://ipm.ucanr.edu/)
- [askextension ostickets](https://osticket.eduworks.com/kb/faq.php?id=675271) (Only questions from the State of California are included)



## Developer resources

- The bot is deployed at http://34.219.35.63:8000/
- [Architecture Diagram](https://docs.google.com/drawings/d/1h_DHiiTr2km3OKpcsoGScElEtyXSR3jL6PHumcRPwQI/edit)
- [Rasa X HTTP API](https://rasa.com/docs/rasa-x/api/rasa-x-http-api/)
- See [Jira AE-314](https://jira.eduworks.us/browse/AE-314) for Rasa X to Gitlab connection.



## Front ends & widgets

- [Messaging and Voice Channels](https://rasa.com/docs/rasa/user-guide/connectors/custom-connectors/#id1)

- [botfront: rasa-webchat *(very popular web widget)*](https://github.com/botfront/rasa-webchat)

- [Custom connectors](https://rasa.com/docs/rasa/user-guide/connectors/custom-connectors)

  