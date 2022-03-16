import logging
from operator import index

from typing import Dict, List, Tuple

import numpy as np

from actions.es import config

logger = logging.getLogger(__name__)

async def _cos_sim_query(
    index           : str           ,
    vector_name     : str           ,
    query_vector    : np.ndarray    ,
    source_query    : dict          ,
    nested          : bool = False  ,
    source_nested   : dict = None
    ) -> dict:
    '''Exectute vector search in ES based on cosine similarity.

    Args:
        index           (str)       : Name of the index.
        vector_name     (str)       : Field vector to be compared against query vector.
        query_vector    (np.ndarray): Query vector.
        source_query    (dict)      : Fields to include in result hits.
        nested          (bool)      : Indication if the query involves nested fields.
        source_nested   (dict)      : Fields to include in 

    Returns:
        dict: Return hits.
    '''    
    cos = f'cosineSimilarity(params.query_vector, "{vector_name}") + 1.0'
    script =  {"source": cos, "params": {"query_vector": query_vector}}


    
    # Query script for single field (without nesting).
    query = {"script_score": {"query" : {"match_all": {}}, "script" : script}}
    
    # Query script for nested fields (path indicates the nested field).
    path = vector_name.split('.')[0]
    query_nested = {
        "nested": {
            "score_mode": "max" ,
            "path"      : path  ,
            "inner_hits": {"size": 1, "name": "nested", "_source": source_nested},
            "query"     : {"function_score": {"script_score": {"script": script}}}
        }
    }

    if not nested:
        response = await config.es_client.search(
            index   = index         ,
            query   = query         ,
            size    = 100            ,
            _source = source_query
        )
    else:
        response = await config.es_client.search(
            index   = index         ,
            query   = query_nested  ,
            size    = 100           ,
            _source = source_query
        )

    hits = response['hits']['hits']
    
    # Add max. scored nested field as a field to main item.
    if nested:
        for item in hits:
            nested = item['inner_hits']['nested']['hits']['hits'][0]['_source']
            item['_source'][path] = item['inner_hits']['nested']['hits']['hits'][0]['_source']  
    
    return hits

async def _handle_es_query(
    question    : str
    ) -> Tuple[dict, dict, dict]:
    '''Perform search in ES base.

    Args:
        question    (str) : Question.

    Returns:
        Tuple[dict, dict, dict]: return tuples for problems, information and askextension matches. 
    '''    
    
    query_vector = config.embed([question]).numpy()[0]
   
    problem_hits        = {}
    information_hits    = {}
    ask_hits            = {}
    
    # ----------------------------------------------- Problem index
    index_config = {
        "index" : "problem",
        "sq"    : {"includes": ["source", "url", "name", "description", "identification", "development", "damage", "management"]},
        "cols"  : ['name', 'description', 'identification', 'development', 'damage', 'management'],
        "nested": [{"name": "links.title", "sq_nested": ['links.type', 'links.title', 'links.src']}]
    }

    for c in index_config['cols']:
        problem_hits[c] = await _cos_sim_query(
            index           = index_config['index']     ,
            vector_name     = c + '_vector'             ,
            query_vector    = query_vector              ,
            source_query    = index_config['sq']
        )
    
    for nested in index_config['nested']:
        problem_hits[nested['name']] = await _cos_sim_query(
            index           = index_config['index']     ,
            vector_name     = nested['name'] + '_vector',   
            query_vector    = query_vector              , 
            source_query    = index_config['sq']        ,
            nested          = True                      ,
            source_nested   = nested['sq_nested']
        )

    # ----------------------------------------------- Information index
    index_config = {
        "index" : "information",
        "sq"    : {"includes": ["source", "url", "name", "description", "management"]},
        "cols"  : ['name', 'description', 'management'],
        "nested": [
            {"name": "links.title"      , "sq_nested": ['links.type', 'links.title', 'links.src']},
            {"name": "problems.title"   , "sq_nested": ['problems.title', 'problems.src'        ]},
        ]
    }

    for c in index_config['cols']:
        information_hits[c] = await _cos_sim_query(
            index           = index_config['index']     ,
            vector_name     = c + '_vector'             ,
            query_vector    = query_vector              ,
            source_query    = index_config['sq']
        )
    
    for nested in index_config['nested']:
        information_hits[nested['name']] = await _cos_sim_query(
            index           = index_config['index']     ,
            vector_name     = nested['name'] + '_vector',   
            query_vector    = query_vector              , 
            source_query    = index_config['sq']        ,
            nested          = True                      ,
            source_nested   = nested['sq_nested']
        )

    # ----------------------------------------------- AskExtension index
    index_config = {
        "index" : "askextension",
        "sq"    : {"includes": ["ticket_no", "url", "created", "title", "question"]},
        "cols"  : ['title_question'],
        "nested": [
            {"name": "tags.tag"         , "sq_nested": ['tags.tag'          ]},
            {"name": "answer.response"  , "sq_nested": ['answer.response'   ]},
        ]
    }
    for c in index_config['cols']:
        ask_hits[c] = await _cos_sim_query(
            index           = index_config['index']     ,
            vector_name     = c + '_vector'             ,
            query_vector    = query_vector              ,
            source_query    = index_config['sq']
        )
    
    for nested in index_config['nested']:
        ask_hits[nested['name']] = await _cos_sim_query(
            index           = index_config['index']     ,
            vector_name     = nested['name'] + '_vector',   
            query_vector    = query_vector              , 
            source_query    = index_config['sq']        ,
            nested          = True                      ,
            source_nested   = nested['sq_nested']
        )
    
    return (problem_hits, information_hits, ask_hits)


def _handle_es_result(
    problem_hits    : dict,
    information_hits: dict,
    ask_hits        : dict
    ) -> Tuple[dict, dict]:
    '''Merge different sources into single source.

    Args:
        problem_hits        (dict): Results from problems data.
        information_hits    (dict): Results from information data.
        ask_hits            (dict): Results from ask extension data.

    Returns:
        Tuple[dict, dict, dict]: Three dictionaries, for problem, 
        information and ask extension results correspondingly.
    '''

    # --------------------------------------- Problem results
    hits = []
    
    cols = ['name', 'description', 'identification', 'development', 'damage', 'management']
    for col in cols:
        for h1 in problem_hits[col]:

            h1['_score_max'] = h1.get('_score', 0.0)
            duplicate = False
            
            for h2 in hits:
                if h1['_id'] == h2['_id']:
                    h2['_score_max'] = max(h2.get('_score_max', 0.0), h1['_score'])

                    duplicate = True
            
            if not duplicate:
                hits.append(h1)

    if len(hits):
        hits = sorted(hits, key = lambda h: h['_score_max'], reverse = True)

    hits_problem = hits

    # --------------------------------------- Information results
    hits = []
    
    cols = ['name', 'description', 'management']
    for col in cols:
        for h1 in information_hits[col]:

            h1['_score_max'] = h1.get('_score', 0.0)
            duplicate = False
            
            for h2 in hits:
                if h1['_id'] == h2['_id']:
                    h2['_score_max'] = max(h2.get('_score_max', 0.0), h1['_score'])

                    duplicate = True
            
            if not duplicate:
                hits.append(h1)

    if len(hits):
        hits = sorted(hits, key = lambda h: h['_score_max'], reverse = True)
    
    hits_information = hits

    # --------------------------------------- Ask Extension results
    hits = []
    
    cols = ['title_question']
    for col in cols:
        for h1 in ask_hits[col]:

            h1['_score_max'] = h1.get('_score', 0.0)
            duplicate = False
            
            for h2 in hits:
                if h1['_id'] == h2['_id']:
                    h2['_score_max'] = max(h2.get('_score_max', 0.0), h1['_score'])

                    duplicate = True
            
            if not duplicate:
                hits.append(h1)

    if len(hits):
        hits = sorted(hits, key = lambda h: h['_score_max'], reverse = True)
    
    hits_ask = hits

    return hits_problem, hits_information, hits_ask


def _weight_score(
    problem_hits    : dict, 
    information_hits: dict,
    ask_hits        : dict
    ) -> Tuple[dict, dict, dict]:
    '''Weight and merge scores.

    Args:
        problem_hits        (dict): Sorted problems data.
        information_hits    (dict): Sorted from information data.
        ask_hits            (dict): Sorted from ask extension data.

    Returns:
        Tuple[dict, dict]: Sorted data with new scores.
    '''    

    ########################################################################
    # For searches in the askextension data, we do not weigh. Already maxed.

    # if len(hits_ask) > 0:
    #     hits_ask = sorted(hits_ask, key=lambda h: h['_score_max'], reverse=True)

    # #######################################################################
    # if len(hits_ipm) > 0:
    #     for hit in hits_ipm:
    #         score_name      = hit.get('_score_name'     , 0.0)
    #         score_other     = hit.get('_score_other'    , 0.0)
    #         score_damage    = hit.get('_score_damage'   , 0.0)

    #         w = [0.8, 0.05, 0.05]

    #         if score_damage < 1.0:
    #             w[0] += 0.5 * w[2]
    #             w[1] += 0.5 * w[2]
    #             w[2] = 0.0

    #         hit['_score_weighted'] = (
    #             w[0] * score_name + w[1] * score_other + w[2] * score_damage
    #         )

    #     # Sort to weighted score
    #     hits_ipm = sorted(hits_ipm, key=lambda h: h['_score_weighted'], reverse=True)

    # Do not filter on threshold. Leave this up to the caller
    return problem_hits, information_hits, ask_hits

def _format_result(
    index           = None,
    score           = None,
    url             = None,
    title           = None,
    description     = None,
    damage          = None,
    identification  = None,
    development     = None,
    management      = None,
    ) -> dict:

    res = {}
    res['title'] = (f'<p>{index+1})<em><a href="{url}" target="_blank">{title}</a></em></br>(score: {score:.2f})</p>')
    res['description'] = ''
    if description:
        res['description'] += (f'<p><strong>Details</strong>: {description[:100]}</p></br>'     )
    if damage:
        res['description'] += (f'<p><strong>Damage</strong>: {damage[:100]}</p></br>'          )
    if identification:
        res['description'] += (f'<p><strong>Identification</strong>: {identification[:100]}</p></br>'  )
    if development:
        res['description'] += (f'<p><strong>Development</strong>: {development[:100]}</p></br>'      )
    if management:
        res['description'] += (f'<p><strong>Management</strong>: {management[:100]}</p></br>'      )
    
    return res

def _get_text(
    problem_hits    : dict,
    information_hits: dict,
    ask_hits        : dict
    ) -> Tuple[dict, dict, dict]:
    '''Print results.

    Args:
        problem_hits        (dict): Sorted results from problems index.
        information_hits    (dict): Sorted results from information index.
        ask_hits            (dict): Sorted results from ask extension index.
    
    Returns:
        Tuple[dict, dict, dict]: Sorted data with new scores.
    '''    
    res_problems    = {
        'text'      : 'Top 3 results from IPM problem sources:',
        'payload'   : 'collapsible',
        'data'      : []
    }

    res_information = {
        'text'      : 'Top 3 results from IPM information sources:',
        'payload'   : 'collapsible',
        'data'      : []
    }

    res_ask         = {
        'text'      : 'Top 3 results from Ask Extension Base:',
        'payload'   : 'collapsible',
        'data'      : []
    }

    if len(problem_hits):
        '''
        Fields:
        "source"
        "url"
        "name"
        "description"
        "identification"
        "development"
        "damage"
        "management"
        '''
            
        for i, h in enumerate(problem_hits[:3]):
            score   = h.get('_score_max', 0.0   )
            source  = h.get('_source'           )

            # group           = source.get("source"           )
            url             = source.get("url"              )
            name            = source.get("name"             )
            description     = source.get("description"      )
            identification  = source.get("identification"   )
            development     = source.get("development"      )
            damage          = source.get("damage"           )
            management      = source.get("management"       )

            res_problems['data'].append(
                _format_result(
                    index           = i             ,
                    score           = score         ,
                    url             = url           ,
                    title           = name          ,
                    description     = description   ,
                    identification  = identification,
                    development     = development   ,
                    damage          = damage        ,
                    management      = management
                )
            )

    if len(information_hits):
        '''
        Fields:
        "source"
        "url"
        "name"
        "description"
        "management"
        '''            
        for i, h in enumerate(information_hits[:3]):
            
            score   = h.get('_score_max', 0.0)
            source  = h.get('_source')

            # group           = source.get("source")
            url             = source.get("url")
            name            = source.get("name")
            description     = source.get("description")
            management      = source.get("management")

            res_information['data'].append(
                _format_result(
                    index           = i             ,
                    score           = score         ,
                    url             = url           ,
                    title           = name          ,
                    description     = description   ,
                    management      = management
                )
            )

    if len(ask_hits):
        '''
        Fields:
        "ticket_no"
        "url""
        "created"
        "title"
        "question"
        '''
            
        for i, h in enumerate(ask_hits[:3]):
            score   = h.get('_score_max', 0.0)
            source  = h.get('_source')

            # ticket_no       = source.get("ticket_no")
            url             = source.get("url")
            # created         = source.get("created")
            title           = source.get("title")
            question        = source.get("question")

            res_ask['data'].append(
                _format_result(
                    index           = i             ,
                    score           = score         ,
                    url             = url           ,
                    title           = title         ,
                    description     = question      ,
                )
            )
    return res_problems, res_information, res_ask

async def submit(
    question    : str,
    ) -> Tuple[dict, dict]:
    
    '''Perform ES query, transform results, print them, and return results.

    Args:
        question    (str): Question that is asked.
        pest_damage (str): Pest damage description.
    
    Returns:
        Tuple[dict, dict]: Sorted data with new scores.
    '''   
    (
        hits_damage     ,
        hits_information,
        hits_ask
    ) = await _handle_es_query(
        question
    )

    (
        hits_damage     ,
        hits_information,
        hits_ask
    ) = _handle_es_result(
        hits_damage     ,
        hits_information,
        hits_ask
    )

    (
        hits_damage     ,
        hits_information,
        hits_ask
    ) = _weight_score(
        hits_damage     ,
        hits_information,
        hits_ask
    )

    res_problems, res_information, res_ask = _get_text(
        hits_damage     ,
        hits_information,
        hits_ask
    )
    
    # _print_hits(hits_ask, 'Ask Extension'   )
    # _print_hits(hits_ipm, 'IPM Data'        )
    
    return res_problems, res_information, res_ask