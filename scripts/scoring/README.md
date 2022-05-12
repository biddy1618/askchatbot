# Container for evaluating query ranking for Ask Extension Chatbot

Script for evaluating the relevancy of queries for Ask Extension Chatbot.

## Running

Run the container with following command:
```bash
docker compose up
```

__NOTE ON URL VALIDATION WHEN RANKING__:
The script strips the parameters of source links from ES database and uses simple string comparison.

## Adapting for MLFlow

Change the necessary lines correspoing to `logger.print(...)`.

## Data format

Data should be available in pickle format. Data transformation script is available under `scoring_data_etl.ipynb` notebook.

It consists of the following columns:

| Question         | ExpectedAnswer                  | URL                                   | Source                         |
|------------------|---------------------------------|---------------------------------------|--------------------------------|
| Questions itself | Reference answer(s) from UC IPM | Link(s) to the problem in UC IPM site | Question source (UC IPM or AE) |

__Notes__:
* If there are several expected answer references they are separated by `\n` (new line) character
* Same applies to URLS - if there are several URLs they are separated by `\n` (new line) character
* All URLs are striped from optional parameters (`?`)
* Line crawled can have two varibles - `Y` and `N`
* Alternative link can be null