# The Extension Bot

Repo for the Ask Extension chatbot component demonstration completed in the 2019-2020 funding cycle.

## Things you can ask the bot

The bot can:
1. Say `hi` & `bye`

   

2. Explain Integrated Pest Management (IPM)

   

3. Find information based on a `pest description` & an optional `damage description`, for example:

   ```bash
   - pest problem description: I have ants in the house 
   - pest damage  description: They create holes in my wall
   ```

   ```bash
   - pest problem description: I think I have lanternflies
   - pest damage  description: -
   ```

   ```bash
   - pest problem description: I have grubs in my lawn 
   - pest damage  description: The grass is completely dead in certain spots
   ```

   

4. Find  information based on an open question, for example:

   ```bash
   - when I import a christmas tree from Michigan to california, is there a tax I need to pay?
   ```

   ```bash
   - Should I desprout potatoes when I store them in the winter?
   ```

   ```bash
   -  have ants in my kitchen and want to know how to get rid of them
   ```

   

5. If the bot cannot find anything, or if the provided information is not helpful, the bot will ask the user if they would like to ask an expert. If yes, a link will be provided where the user can ask their question.



## Data sources

The bot uses data that was scraped from these websites:

- http://ipm.ucanr.edu/
- https://dev.osticket.eduworks.com/  (Only questions from the State of California are included)