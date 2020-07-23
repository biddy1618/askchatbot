"""To view/modify/explore/prepare-for-indexing the askextensiondata json"""
import json
import pprint
from pathlib import Path

# Define the index
index_name = "askextensiondata"  # pylint: disable=invalid-name

DATA_FILE = f"{Path(__file__).parents[1]}/data/{index_name}/{index_name}.json"
DATA_FILE_SMALL = (
    f"{Path(__file__).parents[1]}/data/{index_name}-eda/{index_name}-small.json"
)
DATA_FILE_TOMATO = (
    f"{Path(__file__).parents[1]}/data/{index_name}-eda/{index_name}-tomato.json"
)
DATA_FILE_TOMATO_SPOTS = (
    f"{Path(__file__).parents[1]}/data/{index_name}-eda/{index_name}-tomato-spots.json"
)

EXPORTED_DATA_FILES = [
    f"{Path(__file__).parents[1]}/data/{index_name}/2012-2014.json",
    f"{Path(__file__).parents[1]}/data/{index_name}/2014-2016.json",
    f"{Path(__file__).parents[1]}/data/{index_name}/2016-2018.json",
    f"{Path(__file__).parents[1]}/data/{index_name}/2018-2020.json",
]

"""
Reference conversation
  {
    "faq-id": 1190,
    "title": "Ditch water for organic farming #118171",
    "created": "2013-03-20 19:08:34",
    "updated": "2013-03-29 21:26:34",
    "tags": [
      "irrigation and water management",
      "organic production"
    ],
    "state": "Colorado",
    "county": "Mesa County",
    "question": "I have been told that if I...",
    "answer": {
      "1": {
        "response": "That's ...",
        "author": "Susan Rose"
      },
      "2": {
        "response": "Thank you ...",
        "author": "The Question Asker"
      },
      "3": {
        "response": "Hello. I'm going ...",
        "author": "Cindy Salter"
      },
      "4": {
        "response": "Thank you for ...",
        "author": "The Question Asker"
      },
      "5": {
        "response": "Hello again,See ...",
        "author": "Cindy Salter"
      }
    }
"""


def merge_exported_data_files(exported_data_files, data_file, data_file_small):
    """Combines the exported data files into one. Writes it out in readable format"""
    data = []
    for exported_data_file in exported_data_files:
        with open(exported_data_file) as f:
            data.extend(json.load(f))

    with open(data_file_small, "w") as f:
        json.dump(data[:100], f, indent=2)

    with open(data_file, "w") as f:
        json.dump(data, f, indent=2)


def eda_spots_on_tomato_plants(data_file, data_file_tomato, data_file_tomato_spots):
    """To do exploratory data analysis"""
    with open(data_file) as f:
        data = json.load(f)

    # get all documents with 'tomato' in the title
    docs = []
    docs_spots = []
    for doc in data:
        if "tomato" in doc["title"].lower():
            docs.append(doc)
            if "spots" in doc["title"].lower():
                docs_spots.append(doc)

    with open(data_file_tomato, "w") as f:
        json.dump(docs, f, indent=2)

    with open(data_file_tomato_spots, "w") as f:
        json.dump(docs_spots, f, indent=2)
    ...


if __name__ == "__main__":
    # merge_exported_data_files(EXPORTED_DATA_FILES, DATA_FILE, DATA_FILE_SMALL)
    eda_spots_on_tomato_plants(DATA_FILE, DATA_FILE_TOMATO, DATA_FILE_TOMATO_SPOTS)
