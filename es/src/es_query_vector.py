import logging

from typing import Dict, List, Tuple
from collections import deque
import json

import asyncio

import numpy as np
import pandas as pd

from elasticsearch.helpers import parallel_bulk

import config

logger = logging.getLogger(__name__)


def _cos_sim_query(
    source_query: dict,
    query_vector: np.ndarray,
    vector_name : str     ,
    ) -> dict:
    '''Exectute vector search in ES based on cosine similarity.

    Args:
        source_query (dict): Fields to include in result hits. 
        query_vector (np.ndarray): Query vector.
        vector_name (str): Field vector to be compared against query vector.

    Returns:
        dict: Return hits.
    '''    
    cos = f'cosineSimilarity(params.query_vector, "{vector_name}") + 1.0'

    script_query = {
        "script_score": {
            "query" : {"match_all": {}},
            "script": {"source": cos, "params": {"query_vector": query_vector}}
        }
    }

    response = config.es_client.search(
        index   = config.ES_COMBINED_INDEX,
        query   = script_query,
        size    = 10,
        _source = source_query
    )

    hits = response['hits']['hits']

    return hits


async def _handle_es_query(
    question    : str,
    pest_name   : str,
    pest_desc   : str,
    pest_damage : str
    ) -> Tuple[dict, dict, dict, dict]:
    '''Perform search in ES base.

    Args:
        question (str): Question.
        pest_name (str): Pest name retrieved by Rasa.
        pest_desc (str): Pest description.
        pest_damage (str): Pest damage description.

    Returns:
        Tuple[dict, dict, dict, dict]: return tuples for AE data matches, name matches, other sources matches, and damage matches. 
    '''    
    
    question_vector     = None
    pest_name_vector    = None
    pest_desc_vector    = None
    pest_damage_vector  = None
    
    if question:
        question_vector     = config.embed([question    ]).numpy()[0]
    
    if pest_name:
        pest_name_vector    = config.embed([pest_name   ]).numpy()[0]
    
    if pest_desc:
        pest_desc_vector    = config.embed([pest_desc   ]).numpy()[0]
    else:
        pest_desc_vector = question_vector
    
    if pest_damage:
        pest_damage_vector = config.embed([pest_damage  ]).numpy()[0]
   

    source_query = {
        "includes": [
            "doc_id"    ,
            "name"      ,

            "urlPestDiseaseItems"           ,
            "descriptionPestDiseaseItems"   ,
            "identificationPestDiseaseItems",
            "life_cyclePestDiseaseItems"    ,
            "damagePestDiseaseItems"        ,
            "solutionsPestDiseaseItems"     ,

            "urlTurfPests"                  ,
            "textTurfPests"                 ,

            "urlWeedItems"                  ,
            "descriptionWeedItems"          ,
            
            "urlExoticPests"                ,
            "descriptionExoticPests"        ,
            "damageExoticPests"             ,
            "identificationExoticPests"     ,
            "life_cycleExoticPests"         ,
            "monitoringExoticPests"         ,
            "managementExoticPests"         ,

            "urlPestNote"                   ,
            "urlQuickTipPestNote"           ,
            "descriptionPestNote"           ,
            "life_cyclePestNote"            ,
            "damagePestNote"                ,
            "managementPestNote"            ,
            "contentQuickTipsPestNote"      ,

            "ask_url"                       ,
            "ask_faq_id"                    ,
            "ask_title"                     ,
            "ask_title_question"            ,
            "ask_question"
        ]
    }

    es_ask_hits     = {}
    es_name_hits    = {}
    es_other_hits   = {}
    es_damage_hits  = {}
    # es_caption_hits = {}
    # es_video_hits   = {}

    es_name_hits['name'] = _cos_sim_query(
        source_query    = source_query     ,
        query_vector    = pest_desc_vector ,
        vector_name     = 'name_vector'
    )

    es_name_hits['pest_name'] = []
    if pest_name:
        es_name_hits['pest_name'] = _cos_sim_query(
            source_query    = source_query     ,
            query_vector    = pest_name_vector ,
            vector_name     = 'name_vector'
        )
    
    '''
    Pest Diseases Items

    "descriptionPestDiseaseItems_vector"
    "identificationPestDiseaseItems_vector"
    "life_cyclePestDiseaseItems_vector"
    "damagePestDiseaseItems_vector"
    "solutionsPestDiseaseItems_vector"

    "imagesPestDiseaseItems"    : "caption_vector"
    '''
    es_other_hits['pd_description']     = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'descriptionPestDiseaseItems_vector'
    )

    es_other_hits['pd_identification']  = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'identificationPestDiseaseItems_vector'
    )

    es_other_hits['pd_life_cycle']      = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'life_cyclePestDiseaseItems_vector'
    )

    es_damage_hits['pd_damage_hits'] = []
    if pest_damage:
        es_damage_hits['pd_damage_hits'] = _cos_sim_query(
            source_query    = source_query,
            query_vector    = pest_damage_vector,
            vector_name     = 'damagePestDiseaseItems_vector'
        )
    
    es_other_hits['pd_solutions']       = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'solutionsPestDiseaseItems_vector'
    )

    '''
    Turf Pests

    "textTurfPests_vector"
    "imagesTurfPests": "caption_vector"
    '''
    es_other_hits['tp_text']            = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'textTurfPests_vector'
    )

    '''
    Weed Items

    "descriptionWeedItems_vector"
    "imagesWeedItems": "caption_vector"
    '''
    es_other_hits['wi_text']            = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'descriptionWeedItems_vector'
    )

    '''
    Exotic Pests

    "descriptionExoticPests_vector"
    "damageExoticPests_vector"
    "identificationExoticPests_vector"
    "life_cycleExoticPests_vector"
    "monitoringExoticPests_vector"
    "managementExoticPests_vector"

    "related_linksExoticPests"  : "text_vector"
    "imagesExoticPests"         : "caption_vector"
    '''
    es_other_hits['ep_description']     = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'descriptionExoticPests_vector'
    )

    es_damage_hits['ep_damage'] = []
    if pest_damage:
        es_damage_hits['ep_damage']     = _cos_sim_query(
            source_query    = source_query,
            query_vector    = pest_damage_vector,
            vector_name     = 'damageExoticPests_vector'
        )
    
    es_other_hits['ep_identification']  = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'identificationExoticPests_vector'
    )

    es_other_hits['ep_life_cycle']      = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'life_cycleExoticPests_vector'
    )

    es_other_hits['ep_monitoring']      = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'monitoringExoticPests_vector'
    )

    es_other_hits['ep_management']      = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'managementExoticPests_vector'
    )

    '''
    IPM Data

    "descriptionPestNote_vector"
    "life_cyclePestNote_vector"
    "damagePestNote_vector"
    "managementPestNote_vector"
    "contentQuickTipsPestNote_vector"

    "imageQuickTipsPestNote"    : "caption_vector"
    "imagePestNote"             : "caption_vector"
    "videoPestNote"             : "videoPestNote"
    '''
    es_other_hits['pn_description']     = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'descriptionPestNote_vector'
    )

    es_other_hits['pn_life_cycle']      = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'life_cyclePestNote_vector'
    )

    es_damage_hits['pn_damage'] = []
    if pest_damage:
        es_damage_hits['pn_damage'] = _cos_sim_query(
            source_query    = source_query,
            query_vector    = pest_damage_vector,
            vector_name     = 'damagePestNote_vector'
        )

    es_other_hits['pn_management']      = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'managementPestNote_vector'
    )

    es_other_hits['pn_content_tips']    = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'contentQuickTipsPestNote_vector'
    )

    '''
    AskExtension data
    
    "ask_title_vector"
    "ask_title_question_vector"
    "ask_question_vector"

    "ask_answer" : "response_vector"
    '''

    es_ask_hits['ask_name_title']   = _cos_sim_query(
        source_query    = source_query,
        query_vector    = pest_desc_vector,
        vector_name     = 'ask_title_vector'
    )

    if pest_name:
        es_ask_hits['ask_name_title'] = _cos_sim_query(
            source_query    = source_query,
            query_vector    = pest_name_vector,
            vector_name     = 'ask_title_vector'
        )
    
    es_ask_hits['ask_question'] = []
    if question:
        es_ask_hits['ask_question'] = _cos_sim_query(
            source_query    = source_query,
            query_vector    = question_vector,
            vector_name     = 'ask_title_question_vector'
        )
    
    es_ask_hits['ask_damage'] = []
    if pest_damage:
        es_ask_hits['ask_damage'] = _cos_sim_query(
            source_query    = source_query,
            query_vector    = pest_damage_vector,
            vector_name     = 'ask_title_question_vector'
        )
    
    return (es_ask_hits, es_name_hits, es_other_hits, es_damage_hits)


async def _handle_es_result(
    es_ask_hits     : dict,
    es_name_hits    : dict,
    es_other_hits   : dict,
    es_damage_hits  : dict
    ) -> Tuple[dict, dict]:
    '''Merge different sources into single source.

    Args:
        es_ask_hits (dict): Results from Ask Extension data.
        es_name_hits (dict): Results from name vector comparison.
        es_other_hits (dict): Results from other fields.
        es_damage_hits (dict): Results from damage-related fields.

    Returns:
        Tuple[dict, dict]: Two dictionaries, for Ask Extension results and IPM data results.
    '''
    # ask extension data
    hits = []

    for h1 in (es_ask_hits['ask_name_title'] + es_ask_hits['ask_question'] + es_ask_hits['ask_damage']):
        
        h1['_score_max'] = h1.get('_score', 0.0)
        duplicate = False
        
        for h2 in hits:
            if h1['_source']['doc_id'] == h2['_source']['doc_id']:
                h2['_score_max'] = max(h2.get('_score_max', 0.0), h1['_score'])
                duplicate = True
        
        if not duplicate:
            hits.append(h1)

    if len(hits):
        hits = sorted(hits, key = lambda h: h['_score_max'], reverse = True)

    hits_ask = hits


    # ipm data
    hits = []

    for h1 in (es_name_hits['name'] + es_name_hits['pest_name']):
        
        h1['_score_name'] = h1.get('_score', 0.0)
        duplicate = False

        for h2 in hits:
            if h1['_source']['doc_id'] == h2['_source']['doc_id']:
                h2['_score_name'] = max(h2.get('_score_name', 0.0), h1['_score'])
                duplicate = True
        
        if not duplicate:
            hits.append(h1)

    for h in hits:
        h['_score_other'] = 0.0

    for h in (
        es_other_hits['pd_description'      ] +
        es_other_hits['pd_identification'   ] +
        es_other_hits['pd_life_cycle'       ] +
        es_other_hits['pd_solutions'        ] + 
        es_other_hits['tp_text'             ] + 
        es_other_hits['wi_text'             ] +
        es_other_hits['ep_description'      ] +
        es_other_hits['ep_identification'   ] +
        es_other_hits['ep_life_cycle'       ] +
        es_other_hits['ep_monitoring'       ] +
        es_other_hits['ep_management'       ] +
        es_other_hits['pn_description'      ] +
        es_other_hits['pn_life_cycle'       ] +
        es_other_hits['pn_management'       ] +
        es_other_hits['pn_content_tips'     ]
        ):
        
        h['_score_other'] = h.get('_score', 0.0)
        duplicate = False

        for h2 in hits:
            if h1['_source']['doc_id'] == h2['_source']['doc_id']:
                h2['_score_other'] = max(h2.get('_score_other', 0.0), h1['_score'])
                duplicate = True
        
        if not duplicate:
            hits.append(h1)

    for hit in hits:
            hit["_score_damage"] = 0.0

    for h in (
        es_damage_hits['pd_damage_hits' ] +
        es_damage_hits['ep_damage'      ] +
        es_damage_hits['pn_damage'      ]
        ):

        for h2 in hits:
            if h1['_source']['doc_id'] == h2['_source']['doc_id']:
                h2['_score_damage'] = max(h2.get('_score_damage', 0.0), h1['_score'])
                duplicate = True
        
        if not duplicate:
            hits.append(h1)

    if len(hits):
        hits = sorted(hits, key = lambda h: h['_score'], reverse = True)

    hits_ipm = hits

    return hits_ipm, hits_ask


async def _weight_score(
    hits_ask: dict, 
    hits_ipm: dict
    ) -> Tuple[dict, dict]:
    '''Weight and merge scores.

    Args:
        hits_ask (dict): Results for Ask Extension data.
        hits_ipm (dict): Results for IPM data.

    Returns:
        Tuple[dict, dict]: Sorted data with new scores.
    '''    

    ########################################################################
    # For searches in the askextension data, we do not weigh. Already maxed.

    if len(hits_ask) > 0:
        hits_ask = sorted(hits_ask, key=lambda h: h['_score_max'], reverse=True)

    #######################################################################
    if len(hits_ipm) > 0:
        for hit in hits_ipm:
            score_name      = hit.get('_score_name'     , 0.0)
            score_other     = hit.get('_score_other'    , 0.0)
            score_damage    = hit.get('_score_damage'   , 0.0)

            w = [0.9, 0.05, 0.05]

            if score_damage < 1.0:
                w[0] += 0.5 * w[2]
                w[1] += 0.5 * w[2]
                w[2] = 0.0

            hit['_score_weighted'] = (
                w[0] * score_name + w[1] * score_other + w[2] * score_damage
            )

        # Sort to weighted score
        hits_ipm = sorted(hits_ipm, key=lambda h: h['_score_weighted'], reverse=True)

    # Do not filter on threshold. Leave this up to the caller
    return hits_ask, hits_ipm


def _print_hits(
    hits    : dict, 
    title   : str
    ) -> None:
    '''Print results.

    Args:
        hits (dict): Results to print.
        title (str): Name of the result set.
    '''    

    logger.info("----------------------------------------------------------")
    logger.info(title)
    
    for hit in reversed(hits[:25]):

        if '_score_weighted' not in hit.keys():
            scores = f'score={hit.get("_score_max"  , 0.0):.3f}; '
        else:
            scores = (
                f'wght={hit.get("_score_weighted"   , 0.0):.3f}; '
                f'name={hit.get("_score_name"       , 0.0):.3f}; '
                f'othr={hit.get("_score_other"      , 0.0):.3f}; '
                f'damg={hit.get("_score_damage"     , 0.0):.3f}; '
            )
        text = (
            # f'{hit["_id"]}; '
            f'{scores}'
            f'({hit["_source"]["doc_id"]}, {hit["_source"]["name"]}); '
            f'({hit["_source"]["ask_faq_id"]}, {hit["_source"]["ask_title"]}); '
        )

        pdi_url = hit['_source']['urlPestDiseaseItems'  ]
        tp_url  = hit["_source"]['urlTurfPests'         ]
        wi_url  = hit["_source"]["urlWeedItems"         ]
        ep_url  = hit["_source"]["urlExoticPests"       ]
        pn_url  = hit["_source"]["urlPestNote"          ]
        qt_url  = hit["_source"]["urlQuickTipPestNote"  ]
        ask_url = hit["_source"]["ask_url"              ]

        text = f"{text}URLS:"

        if qt_url:
            text = f"{text} [quick tip]({qt_url}),"
        if pn_url:
            text = f"{text} [pestnote]({pn_url}),"
        if pdi_url:
            text = f"{text} [pest disease item]({pdi_url}),"
        if tp_url:
            text = f"{text} [turf pest]({tp_url}),"
        if wi_url:
            text = f"{text} [weed item]({wi_url})"
        if ep_url:
            text = f"{text} [exotic pests]({ep_url})"
        if ask_url:
            text = f"{text} [askextension]({ask_url})"
        
        logger.info(text)


def query() -> Tuple[str, str, str, str]:
    '''Get input from user

    Returns:
        Tuple[str, str, str, str]: Input from the user - question, pest name, pest description, and pest damage.
    '''   
    question    = None
    pest_name   = None
    pest_descr  = None
    pest_damage = None

    pest_name = input(
        'Enter mapped pest_name that Rasa will extract (Return if none): '
    )
    
    if input('Do you have a question? [y, n] (y): ')        in ['y', '']:
        question    = input('Enter your question: ')
    
    elif input('Do you have a pest problem? [y ,n] (y): ')  in ['y', '']:
        pest_descr  = input('Enter your pest problem description: ')
        
        if input('Is it causing damage? [y, n] (y): ')      in ['y', '']:
            pest_damage = input('Enter damage description: ')
    
    return question, pest_name, pest_descr, pest_damage


async def submit(
    question    : str,
    pest_name   : str,
    pest_desc   : str,
    pest_damage : str
    ) -> Tuple[dict, dict]:
    
    '''Perform ES query, transform results, print them, and return results.

    Args:
        question    (str): Question that is asked.
        pest_name   (str): Name of the pest.
        pest_desc   (str): Pest description.
        pest_damage (str): Pest damage description.
    
    Returns:
        Tuple[dict, dict]: Sorted data with new scores.
    '''   
    (
        es_ask_hits,
        es_name_hits,
        es_other_hits,
        es_damage_hits
    ) = await _handle_es_query(
        question,
        pest_name,
        pest_desc,
        pest_damage
    )

    hits_ask, hits_ipm = await _handle_es_result(
        es_ask_hits,
        es_name_hits,
        es_other_hits,
        es_damage_hits
    )

    hits_ask, hits_ipm = await _weight_score(
        hits_ask, hits_ipm
    )

    _print_hits(hits_ask, 'Ask Extension'   )
    _print_hits(hits_ipm, 'IPM Data'        )
    
    return hits_ask, hits_ipm


async def main():
    '''Run the ES query simulation while there is input from user'''    
    while True:
        try:
            (
                question,
                pest_name,
                pest_desc,
                pest_damage
            ) = query()

            if question or pest_desc:
                await submit(
                    question,
                    pest_name,
                    pest_desc,
                    pest_damage
                )
            else:
                logger.info('Please try again...')
        except KeyboardInterrupt:
            return


def populate_index(recreate: bool = False) -> None:
    '''Populate an index from a CSV file.

    Args:
        recreate (bool, optional): _description_. Defaults to False.
    '''

    # for some reason he uses these files for injecting

    DATA_FILE_NAMES = [
        # 'askextension_transformed.json',
        'pestDiseaseItems_new.json',
        'turfPests.json',
        'weedItems.json',
        'exoticPests.json',
        'ipmdata_new.json',
    ]

    DATA_FILE_NAMES = [config.PATH_DATA_UCIPM + f for f in DATA_FILE_NAMES]
    DATA_FILE_NAMES.append(config.ASKEXTENSION_FILE_RESULT)

    rename_data = {
        "ipmdata_new.json": {
            "name"                  : "name",
            "urlPestNote"           : "urlPestNote",
            "descriptionPestNote"   : "descriptionPestNote",
            "life_cycle"            : "life_cyclePestNote",
            "damagePestNote"        : "damagePestNote",
            "managementPestNote"    : "managementPestNote",
            "imagePestNote"         : "imagePestNote",
            "urlQuickTip"           : "urlQuickTipPestNote",
            "contentQuickTips"      : "contentQuickTipsPestNote",
            "imageQuickTips"        : "imageQuickTipsPestNote",
            "video"                 : "videoPestNote"
        },
        "pestDiseaseItems_new.json": {
            "name"              : "name",
            "url"               : "urlPestDiseaseItems",
            "description"       : "descriptionPestDiseaseItems",
            "identification"    : "identificationPestDiseaseItems",
            "life_cycle"        : "life_cyclePestDiseaseItems",
            "damage"            : "damagePestDiseaseItems",
            "solutions"         : "solutionsPestDiseaseItems",
            "images"            : "imagesPestDiseaseItems",
        },
        "turfPests.json": {
            "name"  : "name",
            "url"   : "urlTurfPests",
            "text"  : "textTurfPests",
            "images": "imagesTurfPests",
        },
        "weedItems.json": {
            "name"          : "name",
            "url"           : "urlWeedItems",
            "description"   : "descriptionWeedItems",
            "images"        : "imagesWeedItems",
        },
        "exoticPests.json": {
            "name"          : "name",
            "url"           : "urlExoticPests",
            "description"   : "descriptionExoticPests",
            "damage"        : "damageExoticPests",
            "identification": "identificationExoticPests",
            "life_cycle"    : "life_cycleExoticPests",
            "monitoring"    : "monitoringExoticPests",
            "management"    : "managementExoticPests",
            "related_links" : "related_linksExoticPests",
            "images"        : "imagesExoticPests", 
        },
        "askextension_transformed.json": {
            "faq-id"        : "ask_faq_id",
            "ticket-no"     : "ask_ticket_no",
            "url"           : "ask_url",
            "title"         : "ask_title",
            "title-question": "ask_title_question",
            "created"       : "ask_created",
            "updated"       : "ask_updated",
            "state"         : "ask_state",
            "county"        : "ask_county",
            "question"      : "ask_question",
            "answer"        : "ask_answer",
        }
    }

    df_docs_json = {}

    logger.info('Reading in files')
    for f in DATA_FILE_NAMES:
        df = pd.read_json(f)
        
        if 'name' in df.columns:
            # for some reason he drops the duplicates from these files
            b_s = df.shape[0]
            df = df.drop_duplicates('name')
            a_s = df.shape[0]
            dropped = b_s - a_s
            
        # we then rename the columns to indicate where those columns is from
        f_name = f.split('/')[-1]
        if f_name in rename_data:
            df = df.rename(columns = rename_data[f_name])
            df = df[rename_data[f_name].values()]
        df_docs_json[f] = df

    # we then concatenate all the data
    logger.info('Concatening...')
    df_docs = pd.concat([df_docs_json[k] for k in df_docs_json.keys()], ignore_index=True)

    # we rename the index by 'doc_id'
    df_docs.index = df_docs.index.set_names('doc_id')
    df_docs.index = df_docs.index.map(str)
    df_docs = df_docs.reset_index()
    df_docs['ask_faq_id'] = df_docs['ask_faq_id'].map(str)
    df_docs['ask_ticket_no'] = df_docs['ask_ticket_no'].map(str)
    
    # we then replace nans and fill nested fields
    logger.info('Filling fields and nested fields...')
    df_docs = df_docs.fillna('')

    columnsNested = ['imagePestNote', 'imageQuickTipsPestNote', 'videoPestNote', 
        'imagesPestDiseaseItems', 'imagesTurfPests', 'imagesWeedItems', 
        'related_linksExoticPests', 'imagesExoticPests', 'ask_answer']

    for c in columnsNested:
        df_docs[c] = [[] if x == '' else x for x in df_docs[c]]

    df_json = df_docs.to_dict('records')
    # docs = docs[:10]

    logger.info('Vectorizing text fields...')
    columnsVectorized = ['name', 'descriptionPestDiseaseItems', 'identificationPestDiseaseItems',
        'life_cyclePestDiseaseItems', 'damagePestDiseaseItems', 'solutionsPestDiseaseItems',
        'textTurfPests', 'descriptionWeedItems', 'descriptionExoticPests', 'damageExoticPests', 
        'identificationExoticPests', 'life_cycleExoticPests', 'monitoringExoticPests', 'managementExoticPests',
        'descriptionPestNote', 'life_cyclePestNote', 'damagePestNote', 'managementPestNote', 
        'contentQuickTipsPestNote', 'ask_title', 'ask_title_question', 'ask_question']

    docs_vectors = {}

    for c in columnsVectorized:
        c_list      = [d[c] for d in df_json]
        c_vectors   = config.embed(c_list).numpy()
        docs_vectors[c] = c_vectors

    for i in range(len(df_json)):
        for c in columnsVectorized:
            df_json[i][c + '_vector'] = docs_vectors[c][i]
    

    
    if recreate:
        logger.info('Deleting existing index...')
        config.es_client.indices.delete(index = config.ES_COMBINED_INDEX, ignore = 404)
    logger.info('Creating new index...')
    config.es_client.indices.create(index = config.ES_COMBINED_INDEX, body=config.ES_COMBINED_VECTOR_MAPPING)        
    logger.info('Inserting data...')
    deque(parallel_bulk(config.es_client, df_json, index = config.ES_COMBINED_INDEX), maxlen = 0)
    config.es_client.indices.refresh()
    success_insertions = config.es_client.cat.count(config.ES_COMBINED_INDEX, params = {"format": "json"})[0]['count']
    logger.info(f'Finished inserting. Succesful insertions: {success_insertions}')
    
    

if __name__ == '__main__':
    # populate_index(recreate = True)

    asyncio.run(main(), debug = True)
    logger.info('Done.')
