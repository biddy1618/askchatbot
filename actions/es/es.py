import logging
from operator import index

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
        source_query (dict)         : Fields to include in result hits. 
        query_vector (np.ndarray)   : Query vector.
        vector_name (str)           : Field vector to be compared against query vector.

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
    pest_damage : str
    ) -> Tuple[dict, dict, dict, dict]:
    '''Perform search in ES base.

    Args:
        question (str)      : Question.
        pest_damage (str)   : Pest damage description.

    Returns:
        Tuple[dict, dict, dict, dict]: return tuples for AE data matches, name matches, other sources matches, and damage matches. 
    '''    
    
    if pest_damage:
        question = '. '.join([question, pest_damage])    
    
    question_vector = config.embed([question]).numpy()[0]
   
    
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
        source_query    = source_query,
        query_vector    = question_vector,
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
        query_vector    = question_vector,
        vector_name     = 'descriptionPestDiseaseItems_vector'
    )

    es_other_hits['pd_identification']  = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
        vector_name     = 'identificationPestDiseaseItems_vector'
    )

    es_other_hits['pd_life_cycle']      = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
        vector_name     = 'life_cyclePestDiseaseItems_vector'
    )

    es_damage_hits['pd_damage_hits'] = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
        vector_name     = 'damagePestDiseaseItems_vector'
    )
    
    es_other_hits['pd_solutions']       = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
        vector_name     = 'solutionsPestDiseaseItems_vector'
    )

    '''
    Turf Pests

    "textTurfPests_vector"
    "imagesTurfPests": "caption_vector"
    '''
    es_other_hits['tp_text']            = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
        vector_name     = 'textTurfPests_vector'
    )

    '''
    Weed Items

    "descriptionWeedItems_vector"
    "imagesWeedItems": "caption_vector"
    '''
    es_other_hits['wi_text']            = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
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
        query_vector    = question_vector,
        vector_name     = 'descriptionExoticPests_vector'
    )

    es_damage_hits['ep_damage']     = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
        vector_name     = 'damageExoticPests_vector'
    )
    
    es_other_hits['ep_identification']  = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
        vector_name     = 'identificationExoticPests_vector'
    )

    es_other_hits['ep_life_cycle']      = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
        vector_name     = 'life_cycleExoticPests_vector'
    )

    es_other_hits['ep_monitoring']      = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
        vector_name     = 'monitoringExoticPests_vector'
    )

    es_other_hits['ep_management']      = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
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
        query_vector    = question_vector,
        vector_name     = 'descriptionPestNote_vector'
    )

    es_other_hits['pn_life_cycle']      = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
        vector_name     = 'life_cyclePestNote_vector'
    )

    es_damage_hits['pn_damage'] = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
        vector_name     = 'damagePestNote_vector'
    )

    es_other_hits['pn_management']      = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
        vector_name     = 'managementPestNote_vector'
    )

    es_other_hits['pn_content_tips']    = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
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
        query_vector    = question_vector,
        vector_name     = 'ask_title_vector'
    )

    es_ask_hits['ask_question'] = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
        vector_name     = 'ask_title_question_vector'
    )

    es_ask_hits['ask_damage'] = _cos_sim_query(
        source_query    = source_query,
        query_vector    = question_vector,
        vector_name     = 'ask_title_question_vector'
    )

    return (es_ask_hits, es_name_hits, es_other_hits, es_damage_hits)

def _handle_es_result(
    es_ask_hits     : dict,
    es_name_hits    : dict,
    es_other_hits   : dict,
    es_damage_hits  : dict
    ) -> Tuple[dict, dict]:
    '''Merge different sources into single source.

    Args:
        es_ask_hits (dict)      : Results from Ask Extension data.
        es_name_hits (dict)     : Results from name vector comparison.
        es_other_hits (dict)    : Results from other fields.
        es_damage_hits (dict)   : Results from damage-related fields.

    Returns:
        Tuple[dict, dict]: Two dictionaries, for Ask Extension results and IPM data results.
    '''

    '''
    ask extension data
    
    es_ask_hits has following keys: ['ask_name_title', 'ask_question', 'ask_damage']
    '''
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

    # new field - _score_max
    hits_ask = hits

    '''
    ipm data - es_name_hits
    
    es_name_hits has following keys: ['name']
    '''
    hits = es_name_hits['name']

    for h1 in hits:
        h1['_score_name']   = h1.get('_score', 0.0)

    
    '''
    ipm data - es_other_hits

    es_other_hits has following keys: 
        # pest diseases - ['pd_description', 'pd_identification', 'pd_life_cycle', 'pd_solutions'   ]
        # turf pests    - ['tp_text']
        # weed items    - ['wi_text']
        # exotic pests  - ['ep_description', 'ep_identification', 'ep_life_cycle', 'ep_monitoring'  , 'ep_management']
        # pest notes    - ['pn_description', 'pn_life_cycle'    , 'pn_management', 'pn_content_tips']
    
    '''
    for h1 in (
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
        
        h1['_score_other'] = h1.get('_score', 0.0)
        duplicate = False

        for h2 in hits:
            if h1['_source']['doc_id'] == h2['_source']['doc_id']:
                h2['_score_other'] = max(h2.get('_score_other', 0.0), h1['_score'])
                duplicate = True
        
        if not duplicate:
            hits.append(h1)

    '''
    ipm data - es_damage_hits
    es_damage_hits has following keys: ['pd_damage_hits', 'ep_damage', 'pn_damage']
    '''
    
    for h1 in (
        es_damage_hits['pd_damage_hits' ] +
        es_damage_hits['ep_damage'      ] +
        es_damage_hits['pn_damage'      ]
        ):

        h1['_score_damage'] = h1.get('_score', 0.0)
        
        for h2 in hits:
            if h1['_source']['doc_id'] == h2['_source']['doc_id']:
                h2['_score_damage'] = max(h2.get('_score_damage', 0.0), h1['_score'])
                duplicate = True
        
        if not duplicate:
            hits.append(h1)
    
    for h in hits:
        h['_score_name'     ] = h.get('_score_name'   , 0.0)
        h['_score_other'    ] = h.get('_score_other'  , 0.0)
        h['_score_damage'   ] = h.get('_score_damage' , 0.0)

    if len(hits):
        hits = sorted(hits, key = lambda h: h['_score'], reverse = True)

    # new fields - _score_name, _score_other, _score_damage
    hits_ipm = hits

    return hits_ask, hits_ipm

def _weight_score(
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

            w = [0.8, 0.05, 0.05]

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


def _format_result(
    index           = None,
    score           = None,
    url             = None,
    title           = None,
    question        = None,
    description     = None,
    damage          = None,
    identification  = None,
    life_cycle      = None,
    monitoring      = None,
    management      = None,
    solutions       = None,
    quicktips       = None
    ) -> str:

    f_text = ('-----------------------------------------</br>')
    f_text += (f'{index+1}) <a href="{url}" target="_blank">{title:>30}</a> (score: {score:.2f})</br>')
    if question:
        f_text += (f'Question          : {question[:100]}</br>'        )
    if description:
        f_text += (f'Description       : {description[:100]}</br>'     )
    if damage:
        f_text += (f'Damage            : {damage[:100]}</br>'          )
    if identification:
        f_text += (f'Identification    : {identification[:100]}</br>'  )
    if life_cycle:
        f_text += (f'Life Cycle        : {life_cycle[:100]}</br>'      )
    if monitoring:
        f_text += (f'Monitoring        : {monitoring[:100]}</br>'      )
    if management:
        f_text += (f'Monitoring        : {management[:100]}</br>'      )
    if solutions:
        f_text += (f'Solutions         : {solutions[:100]}</br>'       )
    if quicktips:
        f_text += (f'Quick Tips        : {quicktips[:100]}</br>'       )
    f_text += ('-----------------------------------------</br></br>')

    return f_text

def _get_text(
    hits_ask: dict, 
    hits_ipm: dict, 
    ) -> None:
    '''Print results.

    Args:
        hits_ask (dict): Results from Ask Extension base.
        hits_ipm (dict): Results from IPM data.
    '''    
    results = ''
    if len(hits_ask):

        results += (f'Found {len(hits_ask)} similar posts from Ask Extension Base.</br>')
        results += (f'Top 3 results:<br>')

        '''
        Fields:
        "ask_url"
        "ask_faq_id"
        "ask_title"
        "ask_title_question"
        "ask_question"
        '''
        for i, h in enumerate(hits_ask[:3]):
            score   = h.get('_score_max', 0.0)
            source  = h.get('_source')

            url         = source.get('ask_url'      )
            title       = source.get('ask_title'    )
            question    = source.get('ask_question' )

            results += _format_result(
                index       = i         ,
                score       = score     ,
                url         = url       ,
                title       = title     ,
                question    = question
            )

    if len(hits_ipm):

        results += (f'Found {len(hits_ipm)} articles from IPM sources</br>')
        results += (f'Top 3 results:</br>')

        for i, h in enumerate(hits_ipm[:3]):
            score   = h.get('_score_weighted', 0.0)
            source  = h.get('_source')

            if source['urlPestDiseaseItems'] != '':
                
                '''
                Fields:
                "name"
                "urlPestDiseaseItems"   
                "descriptionPestDiseaseItems"
                "identificationPestDiseaseItems"
                "life_cyclePestDiseaseItems"
                "damagePestDiseaseItems"
                "solutionsPestDiseaseItems"
                '''
                url             = source.get('urlPestDiseaseItems'              )
                name            = source.get('name'                             )
                description     = source.get('descriptionPestDiseaseItems'      )
                identification  = source.get('identificationPestDiseaseItems'   )
                life_cycle      = source.get('life_cyclePestDiseaseItems'       )
                damage          = source.get('damagePestDiseaseItems'           )
                solutions       = source.get('solutionsPestDiseaseItems'        )

                results += _format_result(
                    index           = i             ,
                    score           = score         ,
                    url             = url           ,
                    title           = name          ,
                    description     = description   ,
                    identification  = identification,
                    life_cycle      = life_cycle    ,
                    damage          = damage        ,
                    solutions       = solutions
                )
                
            elif source['urlTurfPests'] != '': 
                '''
                Fields:
                "name"
                "urlTurfPests"
                "textTurfPests"
                '''
                url             = source.get('urlTurfPests' )
                name            = source.get('name'         )
                description     = source.get('textTurfPests')

                results += _format_result(
                    score           = score         ,
                    url             = url           ,
                    description     = description   ,
                )
                
            elif source['urlWeedItems'] != '':
                '''
                Fields:
                "name"
                "urlWeedItems"
                "descriptionWeedItems"
                '''
                url             = source.get('urlWeedItems'         )
                name            = source.get('name'                 )
                description     = source.get('descriptionWeedItems' )
                
                results += _format_result(
                    index           = i             ,
                    score           = score         ,
                    url             = url           ,
                    title           = name          ,
                    description     = description   ,
                )

            elif source['urlExoticPests'] != '':
                '''
                Fields:
                "name"
                "urlExoticPests"
                "descriptionExoticPests"
                "damageExoticPests"
                "identificationExoticPests"
                "life_cycleExoticPests"
                "monitoringExoticPests"
                "managementExoticPests"
                '''
                url             = source.get('urlExoticPests'               )
                name            = source.get('name'                         )
                description     = source.get('descriptionExoticPests'       )
                damage          = source.get('damageExoticPests'            )
                identification  = source.get('identificationExoticPests'    )
                life_cycle      = source.get('life_cycleExoticPests'        )
                monitoring      = source.get('monitoringExoticPests'        )
                management      = source.get('managementExoticPests'        )
                
                results += _format_result(
                    index           = i             ,
                    score           = score         ,
                    url             = url           ,
                    title           = name          ,
                    description     = description   ,
                    damage          = damage        ,
                    identification  = identification,
                    monitoring      = monitoring    ,
                    life_cycle      = life_cycle    ,
                    management      = management
                )

            elif source['urlPestNote'] != '':
                '''
                Fields:
                "name"
                "urlPestNote"
                "urlQuickTipPestNote"
                "descriptionPestNote"
                "life_cyclePestNote"
                "damagePestNote"
                "managementPestNote"
                "contentQuickTipsPestNote"
                '''
                url             = source.get('urlPestNote'               )
                name            = source.get('name'                      )
                description     = source.get('descriptionPestNote'       )
                life_cycle      = source.get('life_cyclePestNote'        )
                damage          = source.get('damagePestNote'            )
                management      = source.get('managementPestNote'        )
                quicktips       = source.get('contentQuickTipsPestNote'  )

                results += _format_result(
                    index           = i             ,
                    score           = score         ,
                    url             = url           ,
                    title           = name          ,
                    description     = description   ,
                    life_cycle      = life_cycle    ,
                    damage          = damage        ,
                    management      = management    ,
                    quicktips       = quicktips
                )

    return results

async def submit(
    question    : str,
    pest_damage : str
    ) -> Tuple[dict, dict]:
    
    '''Perform ES query, transform results, print them, and return results.

    Args:
        question    (str): Question that is asked.
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
        pest_damage
    )

    hits_ask, hits_ipm = _handle_es_result(
        es_ask_hits,
        es_name_hits,
        es_other_hits,
        es_damage_hits
    )

    hits_ask, hits_ipm = _weight_score(
        hits_ask, hits_ipm
    )

    result_test = _get_text(hits_ask, hits_ipm)
    # _print_hits(hits_ask, 'Ask Extension'   )
    # _print_hits(hits_ipm, 'IPM Data'        )
    
    return result_test