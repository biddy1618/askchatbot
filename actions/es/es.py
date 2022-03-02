import logging

from typing import Dict, List, Tuple

import numpy as np

from actions.es import config

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
        index   = config.es_combined_index,
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

    return hits_ask, hits_ipm


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

    # _print_hits(hits_ask, 'Ask Extension'   )
    # _print_hits(hits_ipm, 'IPM Data'        )
    
    return hits_ask, hits_ipm