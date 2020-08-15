# The Extension Bot

Repo for the Ask Extension chatbot component demonstration completed in the 2019-2020 funding cycle.

## Things you can ask the bot

The bot can:
2. Explain `Integrated Pest Management (IPM)`

2. Find  information based on an open question, for example:

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

   

3. Find information based on a `pest problem description` & an optional `damage description`, for example:

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

   

5. If the chatbot cannot find anything, or if the user indicates that the provided information is not helpful, the bot will ask the user if they would like to ask an expert. If yes, a link will be provided where the user can ask their question to an expert.



## Data sources

The bot uses data that was scraped from these websites:

- http://ipm.ucanr.edu/
- https://dev.osticket.eduworks.com/  (Only questions from the State of California are included)