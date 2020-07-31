"""Create the elasticsearch index for scraped data"""
import json
from pathlib import Path
from elasticsearch.helpers import bulk

import setup_logger  # pylint: disable=unused-import

from actions import actions_config as ac


# Define the index
index_name = ac.ipmdata_index_name


INDEX_FILE = f"{Path(__file__).parents[1]}/data/ipmdata/index.json"

DATA_FILE_NAMES = [
    "cleanedFruitVeggieItems.json",
    "cleanedPestDiseaseItems.json",
    "cleanedPlantFlowerItems.json",
    "cleanedTurfPests.json",
    "cleanedWeedItems.json",
    "ipmdata.json",
]
DATA_FILE_NAMES = [
    "cleanedPestDiseaseItems.json",
    "cleanedTurfPests.json",
    "cleanedWeedItems.json",
    "ipmdata.json",
]

print("-----------------------------------------------------------")
print(f"index_name = {index_name}")
print(f"INDEX_FILE = {INDEX_FILE}")
for DATA_FILE_NAME in DATA_FILE_NAMES:
    print(f"DATA_FILE_NAME  = {DATA_FILE_NAME}")
print("-----------------------------------------------------------")


BATCH_SIZE = 1000
GPU_LIMIT = 0.5


def index_data():
    """Create the index"""
    if index_name in ["ipmdata", "ipmdata-dev"]:
        index_data_ipmdata()
    else:
        raise Exception(f"Not implemented for index_name = {index_name}")


def index_data_ipmdata():
    """Create the index for ipmdata"""
    print(f"Creating the index: {index_name}")
    ac.es_client.indices.delete(index=index_name, ignore=[404])

    with open(INDEX_FILE) as index_file:
        source = index_file.read().strip()
        ac.es_client.indices.create(index=index_name, body=source)

    docs_batch = []
    count = 0

    docs_total = []
    for data_file_name in DATA_FILE_NAMES:
        data_file = f"{Path(__file__).parents[1]}/data/ipmdata/{data_file_name}"
        with open(data_file) as f:
            docs_all = json.load(f)
            docs_total.extend(docs_all)

            docs_batch = []
            for doc in docs_all:

                docs_batch.append(doc)
                count += 1

                if count % BATCH_SIZE == 0:
                    index_batch_ipmdata(docs_batch, data_file_name)
                    docs_batch = []
                    print("Indexed {} documents.".format(count))

            if docs_batch:
                index_batch_ipmdata(docs_batch, data_file_name)
                print("Indexed {} documents.".format(count))

    ac.es_client.indices.refresh(index=index_name)
    print("Done indexing.")

    # check if there are docs with the same name field
    docs_total_names = [doc["name"] for doc in docs_total]
    num_equals = len(docs_total_names) - len(set(docs_total_names))
    if num_equals > 0:
        print("TODO: rewrite things to merge docs that have the same name field")
        print(f"There are {num_equals} equals")


def index_batch_ipmdata(docs, data_file_name):
    """Index a batch of docs"""

    # Update the docs prior to inserting
    # - Note: this will also take care of duplicates found in:
    #    https://jira.eduworks.us/browse/AE-470
    if data_file_name in [
        "ipmdata.json",
        "cleanedFruitVeggieItems.json",
        "cleanedPestDiseaseItems.json",
        "cleanedPlantFlowerItems.json",
        "cleanedTurfPests.json",
        "cleanedWeedItems.json",
    ]:
        docs = rename_fields_to_be_unique(docs, data_file_name)
        docs = update_docs_for_ipmdata(docs)
        ##        docs = update_docs_for_cleanedfruitveggieitems(docs)
        docs = update_docs_for_cleanedpestdiseaseitems(docs)
        ##        docs = update_docs_for_cleanedplantfloweritems(docs)
        docs = update_docs_for_cleanedturfpests(docs)
        docs = update_docs_for_cleanedweeditems(docs)
    else:
        raise Exception(f"Not implemented for data_file_name = {data_file_name}")

    # ingest this batch into the elastic search index
    requests = []
    for doc in docs:
        request = doc
        request["_op_type"] = "index"
        request["_index"] = index_name
        requests.append(request)
    bulk(ac.es_client, requests)


def rename_fields_to_be_unique(docs, data_file_name):
    """some json files have same fields that should be unique"""

    if data_file_name == "ipmdata.json":
        pass
    elif data_file_name == "cleanedFruitVeggieItems.json":
        for doc in docs:
            if "url" in doc.keys():
                doc["urlFruitVeggieItems"] = doc.pop("url")
            if "cultural_tips" in doc.keys():
                doc["cultural_tipsFruitVeggieItems"] = doc.pop("cultural_tips")
            if "pests_and_disorders" in doc.keys():
                doc["pests_and_disordersFruitVeggieItems"] = doc.pop(
                    "pests_and_disorders"
                )
    elif data_file_name == "cleanedPestDiseaseItems.json":
        for doc in docs:
            if "url" in doc.keys():
                doc["urlPestDiseaseItems"] = doc.pop("url")
            if "description" in doc.keys():
                doc["descriptionPestDiseaseItems"] = doc.pop("description")
            if "identification" in doc.keys():
                doc["identificationPestDiseaseItems"] = doc.pop("identification")
            if "life_cycle" in doc.keys():
                doc["life_cyclePestDiseaseItems"] = doc.pop("life_cycle")
            if "damage" in doc.keys():
                doc["damagePestDiseaseItems"] = doc.pop("damage")
            if "solutions" in doc.keys():
                doc["solutionsPestDiseaseItems"] = doc.pop("solutions")
            if "imagesQuickTips" in doc.keys():
                doc["imagesPestDiseaseItems"] = doc.pop("imagesQuickTips")
            if "images" in doc.keys():
                doc["imagesPestDiseaseItems"] = doc.pop("images")
    elif data_file_name == "cleanedPlantFlowerItems.json":
        for doc in docs:
            if "url" in doc.keys():
                doc["urlPlantFlowerItems"] = doc.pop("url")
            if "identification" in doc.keys():
                doc["identificationPlantFlowerItems"] = doc.pop("identification")
            if "optimum_conditions" in doc.keys():
                doc["optimum_conditionsPlantFlowerItems"] = doc.pop(
                    "optimum_conditions"
                )
            if "pests_and_disorders" in doc.keys():
                doc["pests_and_disordersPlantFlowerItems"] = doc.pop(
                    "pests_and_disorders"
                )
            if "imagesQuickTips" in doc.keys():
                doc["imagesPlantFlowerItems"] = doc.pop("imagesQuickTips")
            if "images" in doc.keys():
                doc["imagesPlantFlowerItems"] = doc.pop("images")
    elif data_file_name == "cleanedTurfPests.json":
        for doc in docs:
            if "url" in doc.keys():
                doc["urlTurfPests"] = doc.pop("url")
            if "text" in doc.keys():
                doc["textTurfPests"] = doc.pop("text")
            if "images" in doc.keys():
                doc["imagesTurfPests"] = doc.pop("images")
    elif data_file_name == "cleanedWeedItems.json":
        for doc in docs:
            if "url" in doc.keys():
                doc["urlWeedItems"] = doc.pop("url")
            if "description" in doc.keys():
                doc["descriptionWeedItems"] = doc.pop("description")
            if "images" in doc.keys():
                doc["imagesWeedItems"] = doc.pop("images")
    else:
        raise Exception(f"Not implemented for data_file_name = {data_file_name}")

    return docs


def update_docs_for_ipmdata(docs):
    """Update the docs for ipmdata.json"""

    #########################################
    # use empty values for undefined fields #
    #########################################

    for doc in docs:
        # ipmdata.json
        doc["urlPestNote"] = doc.get("urlPestNote", "")
        doc["descriptionPestNote"] = doc.get("descriptionPestNote", "")
        doc["life_cycle"] = doc.get("life_cycle", "")
        doc["damagePestNote"] = doc.get("damagePestNote", "")
        doc["managementPestNote"] = doc.get("managementPestNote", "")
        doc["contentQuickTips"] = doc.get("contentQuickTips", "")
        doc["imagePestNote"] = doc.get("imagePestNote", {})
        doc["urlQuickTip"] = doc.get("urlQuickTip", "")
        doc["contentQuickTips"] = doc.get("contentQuickTips", "")
        doc["imageQuickTips"] = doc.get("imageQuickTips", {})
        doc["video"] = doc.get("video", {})

    ########################################
    # add embedding vectors for text items #
    ########################################

    pn_names = [doc["name"] for doc in docs]
    pn_name_vectors = ac.embed(pn_names).numpy()

    pn_descriptions = [doc["descriptionPestNote"] for doc in docs]
    pn_description_vectors = ac.embed(pn_descriptions).numpy()

    pn_life_cycles = [doc["life_cycle"] for doc in docs]
    pn_life_cycle_vectors = ac.embed(pn_life_cycles).numpy()

    pn_damages = [doc["damagePestNote"] for doc in docs]
    pn_damage_vectors = ac.embed(pn_damages).numpy()

    pn_managements = [doc["managementPestNote"] for doc in docs]
    pn_management_vectors = ac.embed(pn_managements).numpy()

    qt_contents = [doc["contentQuickTips"] for doc in docs]
    qt_content_vectors = ac.embed(qt_contents).numpy()

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

    for (
        i,
        (
            pn_name_vector,
            pn_description_vector,
            pn_life_cycle_vector,
            pn_damage_vector,
            pn_management_vector,
            qt_content_vector,
            pn_ndl_damage_vector,
        ),
    ) in enumerate(
        zip(
            pn_name_vectors,
            pn_description_vectors,
            pn_life_cycle_vectors,
            pn_damage_vectors,
            pn_management_vectors,
            qt_content_vectors,
            pn_ndl_damage_vectors,
        )
    ):
        docs[i]["name_vector"] = pn_name_vector
        docs[i]["descriptionPestNote_vector"] = pn_description_vector
        docs[i]["life_cycle_vector"] = pn_life_cycle_vector
        docs[i]["damagePestNote_vector"] = pn_damage_vector
        docs[i]["managementPestNote_vector"] = pn_management_vector
        docs[i]["contentQuickTips_vector"] = qt_content_vector
        docs[i]["ndl_damage_vector"] = pn_ndl_damage_vector

    ########################################################
    # add embedding vectors for text items of nested items #
    ########################################################

    for i, doc in enumerate(docs):
        pn_images = docs[i]["imagePestNote"]
        if pn_images:
            captions = [pn_image["caption"] for pn_image in pn_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                docs[i]["imagePestNote"][j]["caption_vector"] = caption_vector

        qt_images = docs[i]["imageQuickTips"]
        if qt_images:
            captions = [qt_image["caption"] for qt_image in qt_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                docs[i]["imageQuickTips"][j]["caption_vector"] = caption_vector

        videos = docs[i]["video"]
        if videos:
            titles = [video["videoTitle"] for video in videos]
            titles_vectors = ac.embed(titles).numpy()
            for j, title_vector in enumerate(titles_vectors):
                docs[i]["video"][j]["videoTitle_vector"] = title_vector

    return docs


def update_docs_for_cleanedfruitveggieitems(docs):
    """Update the docs for cleanedFruitVeggieItems.json"""

    #########################################
    # use empty values for undefined fields #
    #########################################

    for doc in docs:
        doc["urlFruitVeggieItems"] = doc.get("urlFruitVeggieItems", "")
        doc["cultural_tipsFruitVeggieItems"] = doc.get(
            "cultural_tipsFruitVeggieItems", {}
        )
        doc["pests_and_disordersFruitVeggieItems"] = doc.get(
            "pests_and_disordersFruitVeggieItems", {}
        )

    ########################################
    # add embedding vectors for text items #
    ########################################
    fvi_names = [doc["name"] for doc in docs]
    fvi_name_vectors = ac.embed(fvi_names).numpy()

    for (i, fvi_name_vector) in enumerate(fvi_name_vectors):
        docs[i]["name_vector"] = fvi_name_vector

    ########################################################
    # add embedding vectors for text items of nested items #
    ########################################################

    for doc in docs:
        fvi_tips = doc["cultural_tipsFruitVeggieItems"]
        if fvi_tips:
            tips = [fvi_tip["tip"] for fvi_tip in fvi_tips]
            tips_vectors = ac.embed(tips).numpy()
            for j, tip_vector in enumerate(tips_vectors):
                doc["cultural_tipsFruitVeggieItems"][j]["tip_vector"] = tip_vector

        fvi_pds = doc["pests_and_disordersFruitVeggieItems"]
        if fvi_pds:
            pds = [fvi_pd["problem"] for fvi_pd in fvi_pds]
            pds_vectors = ac.embed(pds).numpy()
            for j, pd_vector in enumerate(pds_vectors):
                doc["pests_and_disordersFruitVeggieItems"][j]["pd_vector"] = pd_vector

    return docs


def update_docs_for_cleanedpestdiseaseitems(docs):
    """Update the docs for cleanedPestDiseaseItems.json"""

    #########################################
    # use empty values for undefined fields #
    #########################################

    for doc in docs:
        doc["urlPestDiseaseItems"] = doc.get("urlPestDiseaseItems", "")
        doc["descriptionPestDiseaseItems"] = doc.get("descriptionPestDiseaseItems", "")
        doc["identificationPestDiseaseItems"] = doc.get(
            "identificationPestDiseaseItems", ""
        )
        doc["life_cyclePestDiseaseItems"] = doc.get("life_cyclePestDiseaseItems", "")
        doc["damagePestDiseaseItems"] = doc.get("damagePestDiseaseItems", "")
        doc["solutionsPestDiseaseItems"] = doc.get("solutionsPestDiseaseItems", "")

        doc["imagesPestDiseaseItems"] = doc.get("imagesPestDiseaseItems", {})

    ########################################
    # add embedding vectors for text items #
    ########################################
    pdi_names = [doc["name"] for doc in docs]
    pdi_name_vectors = ac.embed(pdi_names).numpy()

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

    for (
        i,
        (
            pdi_name_vector,
            pdi_description_vector,
            pdi_identification_vector,
            pdi_life_cycle_vector,
            pdi_damage_vector,
            pdi_solution_vector,
        ),
    ) in enumerate(
        zip(
            pdi_name_vectors,
            pdi_description_vectors,
            pdi_identification_vectors,
            pdi_life_cycle_vectors,
            pdi_damage_vectors,
            pdi_solution_vectors,
        )
    ):
        docs[i]["name_vector"] = pdi_name_vector
        docs[i]["descriptionPestDiseaseItems_vector"] = pdi_description_vector
        docs[i]["identificationPestDiseaseItems_vector"] = pdi_identification_vector
        docs[i]["life_cyclePestDiseaseItems_vector"] = pdi_life_cycle_vector
        docs[i]["damagePestDiseaseItems_vector"] = pdi_damage_vector
        docs[i]["solutionsPestDiseaseItems_vector"] = pdi_solution_vector

    ########################################################
    # add embedding vectors for text items of nested items #
    ########################################################

    for doc in docs:
        pdi_images = doc["imagesPestDiseaseItems"]
        if pdi_images:
            captions = [pdi_image["caption"] for pdi_image in pdi_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                doc["imagesPestDiseaseItems"][j]["caption_vector"] = caption_vector

    return docs


def update_docs_for_cleanedplantfloweritems(docs):
    """Update the docs for cleanedPlantFlowerItems.json"""

    #########################################
    # use empty values for undefined fields #
    #########################################

    for doc in docs:
        doc["urlPlantFlowerItems"] = doc.get("urlPlantFlowerItems", "")
        doc["identificationPlantFlowerItems"] = doc.get(
            "identificationPlantFlowerItems", ""
        )
        doc["optimum_conditionsPlantFlowerItems"] = doc.get(
            "optimum_conditionsPlantFlowerItems", ""
        )

        doc["pests_and_disordersPlantFlowerItems"] = doc.get(
            "pests_and_disordersPlantFlowerItems", {}
        )
        doc["imagesPlantFlowerItems"] = doc.get("imagesPlantFlowerItems", {})

    ########################################
    # add embedding vectors for text items #
    ########################################
    pfi_names = [doc["name"] for doc in docs]
    pfi_name_vectors = ac.embed(pfi_names).numpy()

    pfi_identifications = [doc["identificationPlantFlowerItems"] for doc in docs]
    pfi_identification_vectors = ac.embed(pfi_identifications).numpy()

    pfi_conditions = [doc["optimum_conditionsPlantFlowerItems"] for doc in docs]
    pfi_condition_vectors = ac.embed(pfi_conditions).numpy()

    for (
        i,
        (pfi_name_vector, pfi_identification_vector, pfi_condition_vector,),
    ) in enumerate(
        zip(pfi_name_vectors, pfi_identification_vectors, pfi_condition_vectors,)
    ):
        docs[i]["name_vector"] = pfi_name_vector
        docs[i]["identificationPlantFlowerItems_vector"] = pfi_identification_vector
        docs[i]["optimum_conditionsPlantFlowerItems_vector"] = pfi_condition_vector

    ########################################################
    # add embedding vectors for text items of nested items #
    ########################################################

    for doc in docs:
        pfi_pds = doc["pests_and_disordersPlantFlowerItems"]
        if pfi_pds:
            problems = [pfi_pd["problem"] for pfi_pd in pfi_pds]
            problems_vectors = ac.embed(problems).numpy()
            for j, problem_vector in enumerate(problems_vectors):
                doc["pests_and_disordersPlantFlowerItems"][j][
                    "problem_vector"
                ] = problem_vector

        pfi_images = doc["imagesPlantFlowerItems"]
        if pfi_images:
            captions = [pfi_image["caption"] for pfi_image in pfi_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                doc["imagesPlantFlowerItems"][j]["caption_vector"] = caption_vector

    return docs


def update_docs_for_cleanedturfpests(docs):
    """Update the docs for cleanedTurfPests.json"""

    #########################################
    # use empty values for undefined fields #
    #########################################

    for doc in docs:
        doc["urlTurfPests"] = doc.get("urlTurfPests", "")
        doc["textTurfPests"] = doc.get("textTurfPests", "")

        doc["imagesTurfPests"] = doc.get("imagesTurfPests", {})

    ########################################
    # add embedding vectors for text items #
    ########################################
    tp_names = [doc["name"] for doc in docs]
    tp_name_vectors = ac.embed(tp_names).numpy()

    tp_texts = [doc["textTurfPests"] for doc in docs]
    tp_text_vectors = ac.embed(tp_texts).numpy()

    for (i, (tp_name_vector, tp_text_vector,),) in enumerate(
        zip(tp_name_vectors, tp_text_vectors,)
    ):
        docs[i]["name_vector"] = tp_name_vector
        docs[i]["textTurfPests_vector"] = tp_text_vector

    ########################################################
    # add embedding vectors for text items of nested items #
    ########################################################

    for doc in docs:
        tp_images = doc["imagesTurfPests"]
        if tp_images:
            captions = [tp_image["caption"] for tp_image in tp_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                doc["imagesTurfPests"][j]["caption_vector"] = caption_vector

    return docs


def update_docs_for_cleanedweeditems(docs):
    """Update the docs for cleanedWeedItems.json"""

    #########################################
    # use empty values for undefined fields #
    #########################################

    for doc in docs:
        doc["urlWeedItems"] = doc.get("urlWeedItems", "")
        doc["descriptionWeedItems"] = doc.get("descriptionWeedItems", "")

        doc["imagesWeedItems"] = doc.get("imagesWeedItems", {})

    ########################################
    # add embedding vectors for text items #
    ########################################
    wi_names = [doc["name"] for doc in docs]
    wi_name_vectors = ac.embed(wi_names).numpy()

    wi_descriptions = [doc["descriptionWeedItems"] for doc in docs]
    wi_description_vectors = ac.embed(wi_descriptions).numpy()

    for (i, (wi_name_vector, wi_description_vector,),) in enumerate(
        zip(wi_name_vectors, wi_description_vectors,)
    ):
        docs[i]["name_vector"] = wi_name_vector
        docs[i]["descriptionWeedItems_vector"] = wi_description_vector

    ########################################################
    # add embedding vectors for text items of nested items #
    ########################################################

    for doc in docs:
        wi_images = doc["imagesWeedItems"]
        if wi_images:
            captions = [wi_image["caption"] for wi_image in wi_images]
            captions_vectors = ac.embed(captions).numpy()
            for j, caption_vector in enumerate(captions_vectors):
                doc["imagesWeedItems"][j]["caption_vector"] = caption_vector

    return docs


if __name__ == "__main__":
    index_data()
