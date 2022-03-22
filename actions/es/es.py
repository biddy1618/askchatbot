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
        nested          (bool)      : Indication if the query involves nested fields. Defaults to False.
        source_nested   (dict)      : Fields to include in results. Defaults to None.

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
            index   = index                 ,
            query   = query                 ,
            size    = config.es_search_size ,
            _source = source_query
        )
    else:
        response = await config.es_client.search(
            index   = index                 ,
            query   = query_nested          ,
            size    = config.es_search_size ,
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
    ) -> dict:
    '''Merge different sources into single source.

    Args:
        problem_hits        (dict): Results from problems data.
        information_hits    (dict): Results from information data.
        ask_hits            (dict): Results from ask extension data.

    Returns:
        dict: Merged and cut off results.
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

    # --------------------------------------- Score cut off filter and merge
    hits = []

    for h in hits_problem + hits_information + hits_ask:
        if h['_score_max'] > config.es_cut_off + 1:
            hits.append(h)

    if len(hits):
        hits = sorted(hits, key = lambda h: h['_score_max'], reverse = True)

    return hits


def _weight_score(
    hits: dict
    ) -> dict:
    '''Weight and merge scores.

    Args:
        hits (dict): Sorted results.
        
    Returns:
        dict: Sorted data with new scores.
    '''    

    '''
    TO BE IMPLEMENTED
    '''

    return hits


def _format_result(
    index           = None,
    group           = None,
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
    res['title'] = (
        f'<p>{index+1})<em>{title}</a></em></br>'
        f'source: <a href="{url}" target="_blank">{group}</a> index</br>'
        f'(score: {score-1:.2f})</br></p>')
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
    hits    : dict
    ) -> dict:
    '''Print results.

    Args:
        hits (dict): Sorted results from ES query.
        
    Returns:
        dict: Data for chatbot to return.
    '''

    top_n = int(config.es_top_n)
    if len(hits) < config.es_top_n:
        top_n = len(hits)

    res = {
        'text'      : f'Top {top_n} results from data sources:',
        'payload'   : 'collapsible',
        'data'      : []
    }

    if len(hits):
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
        "ticket_no"
        "url""
        "created"
        "title"
        "question"
        
        '''
            
        for i, h in enumerate(hits[:top_n]):
            score   = h.get('_score_max', 0.0   )
            group   = h.get('_index'    , None  )
            source  = h.get('_source'           )

            url             = source.get('url'              , None)
            name            = source.get('name'             , None)
            description     = source.get('description'      , None)
            identification  = source.get('identification'   , None)
            development     = source.get('development'      , None)
            damage          = source.get('damage'           , None)
            management      = source.get('management'       , None)
        
            # ticket_no       = source.get("ticket_no")
            # created         = source.get("created")
            if source.get('title', None):
                name        = source.get('title'            , None)
                description = source.get('question'         , None)

            res['data'].append(
                _format_result(
                    index           = i             ,
                    group           = group         ,
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
    return res

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

    hits = _handle_es_result(
        hits_damage     ,
        hits_information,
        hits_ask
    )

    # hits = _weight_score(hits)

    res = _get_text(hits)
    
    # _print_hits(hits_ask, 'Ask Extension'   )
    # _print_hits(hits_ipm, 'IPM Data'        )
    
    return res

'''
https://ask2.extension.org/kb/faq.php?id=760279

We have small (5mm) reddish brown beetles (species unknown) eating our salvia and basil leaves at night. Is there a safe control such as a powder, spray or oil that is effective at discouraging this pest?

search for the text
search for the slots concatenated
intersect

dealing with out-of-scope text

'''