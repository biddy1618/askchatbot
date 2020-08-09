"""Explore the scraped data"""
import json
from pathlib import Path
import pprint

DATA_FILE_NAMES = [
    "cleanedFruitVeggieItems.json",
    "cleanedPestDiseaseItems.json",
    "cleanedPlantFlowerItems.json",
    "cleanedTurfPests.json",
    "cleanedWeedItems.json",
    "cleanedExoticPests.json",
    "ipmdata.json",
]

DATA_FILE_NAMES_LISTS = [
    "cleanedFruitVeggieItems.json",
    "cleanedPlantFlowerItems.json",
]

DATA_FILE_NAMES_SCRAPEDS = [
    "cleanedPestDiseaseItems.json",
    "cleanedTurfPests.json",
    "cleanedWeedItems.json",
    "cleanedExoticPests.json",
    "ipmdata.json",
]

URLNAME = {
    "cleanedPestDiseaseItems.json": "url",
    "cleanedTurfPests.json": "url",
    "cleanedWeedItems.json": "url",
    "cleanedExoticPests.json": "url",
    "ipmdata.json": "urlPestNote",
}


docs = {}
for data_file_name in DATA_FILE_NAMES:
    data_file = (
        f"{Path(__file__).parents[1]}/elasticsearch/data/ipmdata/{data_file_name}"
    )
    with open(data_file) as f:
        docs[data_file_name] = json.load(f)

# Get links in "pests_and_disorders" of:
# - "cleanedPlantFlowerItems.json"
# - "cleanedFruitVeggieItems.json"
docs_lists = []
for name in DATA_FILE_NAMES_LISTS:
    docs_lists.extend(docs[name])

pad_links_lists = [
    pad["link"] for doc in docs_lists for pad in doc["pests_and_disorders"]
]

pad_links_lists_categories = {"/".join(pl.split("/")[:-1]) for pl in pad_links_lists}
print("--------------------------------------------")
print("All categories in lists type jsons:")
pprint.pprint(pad_links_lists_categories)


# Get links in scraped docs

links_scrapeds = [
    doc[URLNAME[name]] for name in DATA_FILE_NAMES_SCRAPEDS for doc in docs[name]
]

links_scrapeds_categories = {"/".join(pl.split("/")[:-1]) for pl in links_scrapeds}
print("--------------------------------------------")
print("All categories in scraped type jsons:")
pprint.pprint(links_scrapeds_categories)

# check the scraped categories
scraped_categories = [
    c for c in pad_links_lists_categories if c in links_scrapeds_categories
]
print("--------------------------------------------")
print("Scraped categories:")
pprint.pprint(scraped_categories)

# check the unscraped categories
unscraped_categories = [
    c for c in pad_links_lists_categories if c not in links_scrapeds_categories
]
print("--------------------------------------------")
print("Unscraped categories:")
pprint.pprint(unscraped_categories)
