# Ingesting data into the ES

## Downloading data

### AskExtension knowledge base data

Crawled data can be found [here](https://drive.google.com/drive/folders/12CyhdvCwNLgtdUHTcmWkAKR4oIWhGKHq).

Download data in the folder `8/3 JSON Export` and put downloaded files into local folder at `actions/es/data/askextension/2020-08-20`.

### UC IPM crawled data

Data can be obtained through DVC ([installation guide](https://wiki.eduworks.com/Information_Technology/MLOps/DATA-Installing-DVC)). Clone the [repository](https://git.eduworks.us/data/ask-extension/uc-ipm-web-scrape) for scraped data, install Google Cloud Client - `gcloud` (more in installation guide), authenticate, and pull the data through dvc. Please, contact admin for access rights.

Copy the downloaded files into folder `actions/es/data/uc-ipm/updated-Dec2021`.

## Ingesting data

Run the scripts in the [notebook](es_ingest_data.ipynb) to create indexes and ingest data sources from AE and UC IPM.

Run the scripts in the [notebook](es_chat_logging_index.ipynb) to create index for chat history.
