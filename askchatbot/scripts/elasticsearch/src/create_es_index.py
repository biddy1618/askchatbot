"""Create the elasticsearch index for scraped data"""
from pathlib import Path
from elasticsearch.helpers import bulk
import pandas as pd

import setup_logger  # pylint: disable=unused-import

from actions import actions_config as ac

pd.set_option("display.max_columns", 100)
pd.set_option("display.width", 1000)
# pd.set_option('display.max_colwidth', None)
pd.set_option("display.max_colwidth", 80)


# Define the index
index_name = ac.ipmdata_index_name


INDEX_FILE = f"{Path(__file__).parents[1]}/data/ipmdata/index.json"

DATA_FILE_NAMES = [
    "askextensiondata-california.json",
    "cleanedPestDiseaseItems.json",
    "cleanedTurfPests.json",
    "cleanedWeedItems.json",
    "cleanedExoticPests.json",
    "ipmdata.json",
]

print("-----------------------------------------------------------")
print(f"index_name = {index_name}")
print(f"INDEX_FILE = {INDEX_FILE}")
for DATA_FILE_NAME in DATA_FILE_NAMES:
    print(f"DATA_FILE_NAME  = {DATA_FILE_NAME}")
print("-----------------------------------------------------------")


BATCH_SIZE = 10
GPU_LIMIT = 0.5


def index_data():
    """Create the index"""
    if index_name in [
        "ipmdata",
        "ipmdata-dev",
        "ipmdata-dev-large-5",
        "ipm-and-ask-large-5",
    ]:
        index_data_ipmdata()
    else:
        raise Exception(f"Not implemented for index_name = {index_name}")


def index_data_ipmdata():
    """Create the index for ipmdata"""

    df_docs = docs_etl()

    print(f"Creating the index: {index_name}")
    ac.es_client.indices.delete(index=index_name, ignore=[404])

    with open(INDEX_FILE) as index_file:
        source = index_file.read().strip()
        ac.es_client.indices.create(index=index_name, body=source)

    docs_batch = []
    count = 0

    docs = df_docs.reset_index().to_dict("records")

    print("Indexing...")
    docs_batch = []
    for doc in docs:

        docs_batch.append(doc)
        count += 1

        if count % BATCH_SIZE == 0:
            index_batch_ipmdata(docs_batch)
            docs_batch = []
            print("Indexed {} documents.".format(count))

    if docs_batch:
        index_batch_ipmdata(docs_batch)
        print("Indexed {} documents.".format(count))

    ac.es_client.indices.refresh(index=index_name)
    print("Done indexing.")


def docs_etl():
    """Read all docs and pre-process them"""
    print("ETL for docs...")

    df_docs_json = {}
    for data_file_name in DATA_FILE_NAMES:
        path_data = f"{Path(__file__).parents[1]}/data/ipmdata/{data_file_name}"
        df_docs_json[data_file_name] = pd.read_json(path_data)

        if 'name' in df_docs_json[data_file_name].columns:
            before_shape = df_docs_json[data_file_name].shape
            df_docs_json[data_file_name] = df_docs_json[data_file_name].drop_duplicates(
                "name"
            )
            after_shape = df_docs_json[data_file_name].shape
            num_dropped = before_shape[0] - after_shape[0]
            if num_dropped > 0:
                print(f"Dropped {num_dropped} with same 'name' in {data_file_name}")

    df_docs_json = unique_column_names(df_docs_json)

    df_docs = concat_docs(df_docs_json)

    df_docs.index = df_docs.index.set_names("doc_id")

    df_docs = replace_nan(df_docs)

    return df_docs


def index_batch_ipmdata(docs):
    """Index a batch of docs"""

    docs = create_embedding_vectors(docs)

    # ingest this batch into the elastic search index
    requests = []
    for doc in docs:
        request = doc
        request["_op_type"] = "index"
        request["_index"] = index_name
        requests.append(request)
    bulk(ac.es_client, requests)


def unique_column_names(df_docs_json):
    """Column names must be unique and identify the file they came from"""

    df_docs_json["cleanedPestDiseaseItems.json"] = df_docs_json[
        "cleanedPestDiseaseItems.json"
    ].rename(
        columns={
            "url": "urlPestDiseaseItems",
            "description": "descriptionPestDiseaseItems",
            "identification": "identificationPestDiseaseItems",
            "life_cycle": "life_cyclePestDiseaseItems",
            "damage": "damagePestDiseaseItems",
            "solutions": "solutionsPestDiseaseItems",
            "imagesQuickTips": "imagesQuickTipsPestDiseaseItems",
            "images": "imagesPestDiseaseItems",
            "other_headers": "other_headersPestDiseaseItems",
        }
    )

    df_docs_json["cleanedTurfPests.json"] = df_docs_json[
        "cleanedTurfPests.json"
    ].rename(
        columns={
            "url": "urlTurfPests",
            "text": "textTurfPests",
            "images": "imagesTurfPests",
        }
    )

    df_docs_json["cleanedWeedItems.json"] = df_docs_json[
        "cleanedWeedItems.json"
    ].rename(
        columns={
            "url": "urlWeedItems",
            "description": "descriptionWeedItems",
            "images": "imagesWeedItems",
        }
    )

    df_docs_json["cleanedExoticPests.json"] = df_docs_json[
        "cleanedExoticPests.json"
    ].rename(
        columns={
            "url": "urlExoticPests",
            "description": "descriptionExoticPests",
            "damage": "damageExoticPests",
            "identification": "identificationExoticPests",
            "life_cycle": "life_cycleExoticPests",
            "monitoring": "monitoringExoticPests",
            "management": "managementExoticPests",
            "related_links": "related_linksExoticPests",
            "images": "imagesExoticPests",
        }
    )

    df_docs_json["askextensiondata-california.json"] = df_docs_json[
        "askextensiondata-california.json"
    ].rename(
        columns={
            "faq-id": "ask_faq_id",
            "url": "ask_url",
            "title": "ask_title",
            "title-question": "ask_title_question",
            "created": "ask_created",
            "updated": "ask_updated",
            "state": "ask_state",
            "county": "ask_county",
            "question": "ask_question",
            "answer": "ask_answer",
        }
    )

    ##    df_docs_json["cleanedFruitVeggieItems.json"] = df_docs_json[
    ##        "cleanedFruitVeggieItems.json"
    ##    ].rename(
    ##        columns={
    ##            "url": "urlFruitVeggieItems",
    ##            "cultural_tips": "cultural_tipsFruitVeggieItems",
    ##            "pests_and_disorders": "pests_and_disordersFruitVeggieItems",
    ##        }
    ##    )

    ##    df_docs_json["cleanedPlantFlowerItems.json"] = df_docs_json[
    ##        "cleanedPlantFlowerItems.json"
    ##    ].rename(
    ##        columns={
    ##            "url": "urlPlantFlowerItems",
    ##            "identification": "identificationPlantFlowerItems",
    ##            "optimum_conditions": "optimum_conditionsPlantFlowerItems",
    ##            "pests_and_disorders": "pests_and_disordersPlantFlowerItems",
    ##            "imagesQuickTips": "imagesPlantFlowerItems",
    ##            "images": "imagesPlantFlowerItems",
    ##        }
    ##    )

    return df_docs_json


def concat_docs(df_docs_json):
    """Concatenate the docs of different json files into one big dataframe"""
    df_docs = pd.concat(
        [df_docs_json[name] for name in DATA_FILE_NAMES], ignore_index=True
    )
    return df_docs


def replace_nan(df_docs):
    """Replace all NaN values in the dataframe with appropriate content"""
    df_docs = df_docs.fillna("")
    # nested types require an empty list if non existing
    for column in [
        "imagePestNote",
        "imageQuickTips",
        "video",
        "imagesPestDiseaseItems",
        "other_headersPestDiseaseItems",
        "imagesTurfPests",
        "imagesWeedItems",
        "related_linksExoticPests",
        "imagesExoticPests",
        "ask_answer",
    ]:
        df_docs[column] = [[] if x == "" else x for x in df_docs[column]]

    return df_docs


def create_embedding_vectors(docs):
    """Add the embedding vectors to the docs"""

    print(f"Creating embeddings for {len(docs)} documents...")

    ########################################
    # add embedding vectors for text items #
    ########################################
    names = [doc["name"] for doc in docs]
    name_vectors = ac.embed(names).numpy()

    pn_descriptions = [doc["descriptionPestNote"] for doc in docs]
    pn_description_vectors = ac.embed(pn_descriptions).numpy()

    pn_life_cycles = [doc["life_cycle"] for doc in docs]
    pn_life_cycle_vectors = ac.embed(pn_life_cycles).numpy()

    pn_damages = [doc["damagePestNote"] for doc in docs]
    pn_damage_vectors = ac.embed(pn_damages).numpy()

    pn_managements = [doc["managementPestNote"] for doc in docs]
    pn_management_vectors = ac.embed(pn_managements).numpy()

    # damage by itself might not work.
    # also encode it together with name, description, life_cycle
    pn_ndl_damage = [
        doc["name"]
        + doc["descriptionPestNote"]
        + doc["life_cycle"]
        + doc["damagePestNote"]
        for doc in docs
    ]
    pn_ndl_damage_vectors = ac.embed(pn_ndl_damage).numpy()

    qt_contents = [doc["contentQuickTips"] for doc in docs]
    qt_content_vectors = ac.embed(qt_contents).numpy()

    pdi_descriptions = [doc["descriptionPestDiseaseItems"] for doc in docs]
    pdi_description_vectors = ac.embed(pdi_descriptions).numpy()

    pdi_identifications = [doc["identificationPestDiseaseItems"] for doc in docs]
    pdi_identification_vectors = ac.embed(pdi_identifications).numpy()

    pdi_life_cycles = [doc["life_cyclePestDiseaseItems"] for doc in docs]
    pdi_life_cycle_vectors = ac.embed(pdi_life_cycles).numpy()

    pdi_damages = [doc["damagePestDiseaseItems"] for doc in docs]
    pdi_damage_vectors = ac.embed(pdi_damages).numpy()

    pdi_solutions = [doc["solutionsPestDiseaseItems"] for doc in docs]
    pdi_solution_vectors = ac.embed(pdi_solutions).numpy()

    tp_texts = [doc["textTurfPests"] for doc in docs]
    tp_text_vectors = ac.embed(tp_texts).numpy()

    wi_descriptions = [doc["descriptionWeedItems"] for doc in docs]
    wi_description_vectors = ac.embed(wi_descriptions).numpy()

    ep_descriptions = [doc["descriptionExoticPests"] for doc in docs]
    ep_description_vectors = ac.embed(ep_descriptions).numpy()

    ep_damages = [doc["damageExoticPests"] for doc in docs]
    ep_damage_vectors = ac.embed(ep_damages).numpy()

    ep_identifications = [doc["identificationExoticPests"] for doc in docs]
    ep_identification_vectors = ac.embed(ep_identifications).numpy()

    ep_life_cycles = [doc["life_cycleExoticPests"] for doc in docs]
    ep_life_cycle_vectors = ac.embed(ep_life_cycles).numpy()

    ep_monitorings = [doc["monitoringExoticPests"] for doc in docs]
    ep_monitoring_vectors = ac.embed(ep_monitorings).numpy()

    ep_managements = [doc["managementExoticPests"] for doc in docs]
    ep_management_vectors = ac.embed(ep_managements).numpy()

    ask_titles = [doc["ask_title"] for doc in docs]
    ask_title_vectors = ac.embed(ask_titles).numpy()

    ask_title_questions = [doc["ask_title_question"] for doc in docs]
    ask_title_question_vectors = ac.embed(ask_title_questions).numpy()

    ask_questions = [doc["ask_question"] for doc in docs]
    ask_question_vectors = ac.embed(ask_questions).numpy()

    for (
        i,
        (
            name_vector,
            pn_description_vector,
            pn_life_cycle_vector,
            pn_damage_vector,
            pn_management_vector,
            qt_content_vector,
            pn_ndl_damage_vector,
            pdi_description_vector,
            pdi_identification_vector,
            pdi_life_cycle_vector,
            pdi_damage_vector,
            pdi_solution_vector,
            tp_text_vector,
            wi_description_vector,
            ep_description_vector,
            ep_damage_vector,
            ep_identification_vector,
            ep_life_cycle_vector,
            ep_monitoring_vector,
            ep_management_vector,
            ask_title_vector,
            ask_title_question_vector,
            ask_question_vector,
        ),
    ) in enumerate(
        zip(
            name_vectors,
            pn_description_vectors,
            pn_life_cycle_vectors,
            pn_damage_vectors,
            pn_management_vectors,
            qt_content_vectors,
            pn_ndl_damage_vectors,
            pdi_description_vectors,
            pdi_identification_vectors,
            pdi_life_cycle_vectors,
            pdi_damage_vectors,
            pdi_solution_vectors,
            tp_text_vectors,
            wi_description_vectors,
            ep_description_vectors,
            ep_damage_vectors,
            ep_identification_vectors,
            ep_life_cycle_vectors,
            ep_monitoring_vectors,
            ep_management_vectors,
            ask_title_vectors,
            ask_title_question_vectors,
            ask_question_vectors,
        )
    ):
        docs[i]["name_vector"] = name_vector
        docs[i]["descriptionPestNote_vector"] = pn_description_vector
        docs[i]["life_cycle_vector"] = pn_life_cycle_vector
        docs[i]["damagePestNote_vector"] = pn_damage_vector
        docs[i]["managementPestNote_vector"] = pn_management_vector
        docs[i]["contentQuickTips_vector"] = qt_content_vector
        docs[i]["ndl_damage_vector"] = pn_ndl_damage_vector
        docs[i]["descriptionPestDiseaseItems_vector"] = pdi_description_vector
        docs[i]["identificationPestDiseaseItems_vector"] = pdi_identification_vector
        docs[i]["life_cyclePestDiseaseItems_vector"] = pdi_life_cycle_vector
        docs[i]["damagePestDiseaseItems_vector"] = pdi_damage_vector
        docs[i]["solutionsPestDiseaseItems_vector"] = pdi_solution_vector
        docs[i]["textTurfPests_vector"] = tp_text_vector
        docs[i]["descriptionWeedItems_vector"] = wi_description_vector
        docs[i]["descriptionExoticPests_vector"] = ep_description_vector
        docs[i]["damageExoticPests_vector"] = ep_damage_vector
        docs[i]["identificationExoticPests_vector"] = ep_identification_vector
        docs[i]["life_cycleExoticPests_vector"] = ep_life_cycle_vector
        docs[i]["monitoringExoticPests_vector"] = ep_monitoring_vector
        docs[i]["managementExoticPests_vector"] = ep_management_vector
        docs[i]["ask_title_vector"] = ask_title_vector
        docs[i]["ask_title_question_vector"] = ask_title_question_vector
        docs[i]["ask_question_vector"] = ask_question_vector

    ########################################################
    # add embedding vectors for text items of nested items #
    ########################################################
    for doc in docs:
        pn_images = doc["imagePestNote"]
        if pn_images:
            captions = [pn_image["caption"] for pn_image in pn_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                doc["imagePestNote"][j]["caption_vector"] = caption_vector

        qt_images = doc["imageQuickTips"]
        if qt_images:
            captions = [qt_image["caption"] for qt_image in qt_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                doc["imageQuickTips"][j]["caption_vector"] = caption_vector

        videos = doc["video"]
        if videos:
            titles = [video["videoTitle"] for video in videos]
            titles_vectors = ac.embed(titles).numpy()
            for j, title_vector in enumerate(titles_vectors):
                doc["video"][j]["videoTitle_vector"] = title_vector

        pdi_images = doc["imagesPestDiseaseItems"]
        if pdi_images:
            captions = [pdi_image["caption"] for pdi_image in pdi_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                doc["imagesPestDiseaseItems"][j]["caption_vector"] = caption_vector

        pdi_other_headers = doc["other_headersPestDiseaseItems"]
        if pdi_other_headers:
            headers = [
                pdi_other_header["header"] for pdi_other_header in pdi_other_headers
            ]
            headers_vectors = ac.embed(headers).numpy()
            texts = [pdi_other_header["text"] for pdi_other_header in pdi_other_headers]
            texts_vectors = ac.embed(texts).numpy()
            for j, (header_vector, text_vector) in enumerate(
                zip(headers_vectors, texts_vectors)
            ):
                doc["other_headersPestDiseaseItems"][j]["header_vector"] = header_vector
                doc["other_headersPestDiseaseItems"][j]["text_vector"] = text_vector

        tp_images = doc["imagesTurfPests"]
        if tp_images:
            captions = [tp_image["caption"] for tp_image in tp_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                doc["imagesTurfPests"][j]["caption_vector"] = caption_vector

        wi_images = doc["imagesWeedItems"]
        if wi_images:
            captions = [wi_image["caption"] for wi_image in wi_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                doc["imagesWeedItems"][j]["caption_vector"] = caption_vector

        ep_related_links = doc["related_linksExoticPests"]
        if ep_related_links:
            texts = [ep_related_link["text"] for ep_related_link in ep_related_links]
            texts_vectors = ac.embed(texts).numpy()
            for j, text_vector in enumerate(texts_vectors):
                doc["related_linksExoticPests"][j]["text_vector"] = text_vector

        ep_images = doc["imagesExoticPests"]
        if ep_images:
            captions = [ep_image["caption"] for ep_image in ep_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                doc["imagesExoticPests"][j]["caption_vector"] = caption_vector

        ask_answers = doc["ask_answer"]
        if ask_answers:
            responses = [ask_answer["response"] for ask_answer in ask_answers]
            responses_vectors = ac.embed(responses).numpy()
            for j, response_vector in enumerate(responses_vectors):
                doc["ask_answer"][j]["response_vector"] = response_vector

    return docs


if __name__ == "__main__":
    index_data()
