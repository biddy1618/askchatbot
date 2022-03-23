import logging
from operator import index

from typing import Dict, List, Tuple

import numpy as np

from actions.es import config

logger = logging.getLogger(__name__)

async def _cos_sim_query(
    index           : str               ,
    query_vector    : np.ndarray        ,
    query_links     : bool      = False ,           
    filter_ids      : List[str] = None  ,
    ) -> dict:
    '''Exectute vector search in ES based on cosine similarity.

    Args:
        index           (str)       : Name of the index.
        query_vector    (np.ndarray): Query vector.
        query_link      (bool)      : True if querying against links. Defaults to False.
        filter_ids      (List[str]) : Filter results based on the IDs given. Defaults to None.

    Returns:
        dict: Return hits.
    '''
    vector_name     = 'vectors.vector'
    source_nested   = ['vectors.name']
    if query_links:
        vector_name = 'vectors_links.vector'
        source_nested   = ['vectors_links.order']
        
    cos     = f'cosineSimilarity(params.query_vector, "{vector_name}") + 1.0'
    script  = {"source": cos, "params": {"query_vector": query_vector}}
    
    source_query = {'includes': [
        'source', 'url', 'name', 'description', 'identification', 
        'development', 'damage', 'management', 'links'
    ]}

    path = vector_name.split('.')[0]
    query = {"bool": {
        "must": {"nested": {
                    "score_mode": "max" ,
                    "path"      : path  ,
                    "inner_hits": {"size": 3, "name": "nested", "_source": source_nested},
                    "query"     : {"function_score": {"script_score": {"script": script}}}}
        },
        "filter"    : [],
        "must_not"  : []
    }}

    if filter_ids is not None:
        query['bool']['filter'  ].append({'ids'     : {'values': filter_ids     }})

    response = await config.es_client.search(
        index   = index                 ,
        query   = query                 ,
        size    = config.es_search_size ,
        _source = source_query
    )

    hits = []

    for h1 in response['hits']['hits']:
        top_scores = []

        for h2 in h1['inner_hits']['nested']['hits']['hits']:
            top_scores.append({'score': h2['_score'] - 1, 'source': h2['_source']})
        
        h1['_source']['top_scores'  ] = top_scores
        h1['_source']['_id'         ] = h1['_id'    ]
        h1['_source']['_score'      ] = h1['_score' ] - 1
        
        hits.append(h1['_source'])

    return hits


async def _handle_es_query(
    question: str       ,
    slots   : str = None,
    ) -> dict:
    '''Perform search in ES base.

    Args:
        question (str)  : Query statement.
        slots    (str)  : Extracted slots. Defaults to None.

    Returns:
        dict    : return tuples for problems, information and askextension matches. 
    '''    
    
    query_vector = config.embed([question]).numpy()[0]
    
    hits        = []
    hits_slots  = []

    hits = await _cos_sim_query(
        index           = config.es_combined_index  ,
        query_vector    = query_vector              ,
    )

    for h in hits: 
        if h['source'] == 'askExtension': 
            h['_score'] *= config.es_ask_weight
            
    hits = [h for h in hits if h['_score'] > config.es_cut_off]
 
    if slots:
        slots_vector = config.embed([slots]).numpy()[0]
        filter_ids = [h['_id'] for h in hits]

        hits_slots = await _cos_sim_query(
            index           = config.es_combined_index  ,
            query_vector    = slots_vector              ,
            filter_ids      = filter_ids
    )


    return hits, hits_slots


def _format_result(
    index           = None,
    source          = None,
    score           = None,
    url             = None,
    name            = None,
    description     = None,
    damage          = None,
    identification  = None,
    development     = None,
    management      = None,
    ) -> dict:

    res = {}
    res['title'] = (
        f'<p>{index+1})<em>{name}</a></em>'
        f'</br>(score: {score:.2f})</br>'
        f'(source: <a href="{url}" target="_blank">{source}</a></p>')
    res['description'] = ''
    if description:
        res['description'] += (f'<p><strong>Details</strong>: {description[:100]}</p></br>'             )
    if damage:
        res['description'] += (f'<p><strong>Damage</strong>: {damage[:100]}</p></br>'                   )
    if identification:
        res['description'] += (f'<p><strong>Identification</strong>: {identification[:100]}</p></br>'   )
    if development:
        res['description'] += (f'<p><strong>Development</strong>: {development[:100]}</p></br>'         )
    if management:
        res['description'] += (f'<p><strong>Management</strong>: {management[:100]}</p></br>'           )
    
    return res

def _get_text(hits: dict) -> dict:
    '''Process results for output.

    Args:
        hits (dict): Sorted results from ES query.
        
    Returns:
        dict: Data for chatbot to return.
    '''

    top_n = config.es_top_n
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
        '''
            
        for i, h in enumerate(hits[:top_n]):
            score           = h.get('_score'        , 0.0   )
            source          = h.get('source'        , None  )
            url             = h.get('url'           , None  )
            name            = h.get('name'          , None  )
            description     = h.get('description'   , None  )
            identification  = h.get('identification', None  )
            development     = h.get('development'   , None  )
            damage          = h.get('damage'        , None  )
            management      = h.get('management'    , None  )
        
            res['data'].append(
                _format_result(
                    index           = i             ,
                    source          = source        ,
                    score           = score         ,
                    url             = url           ,
                    name            = name          ,
                    description     = description   ,
                    identification  = identification,
                    development     = development   ,
                    damage          = damage        ,
                    management      = management
                )
            )   
    
    return res

async def submit(
    question: str       ,
    slots   : str = None
    ) -> Tuple[dict, dict]:
    
    '''Perform ES query, transform results, print them, and return results.

    Args:
        question    (str): Question that is asked.
        slots       (str): Pest damage description. Defaults to None.
    
    Returns:
        Tuple[dict, dict]: Results from ES query. If slots were provided, then results with slots refinement.
    '''   
    hits, hits_slots = await _handle_es_query(question, slots = slots)
    
    res         = _get_text(hits)
    res_slots   = None
    if slots:
        res_slots = _get_text(hits_slots)
    
    return res, res_slots

'''
https://ask2.extension.org/kb/faq.php?id=760279

We have small (5mm) reddish brown beetles (species unknown) eating our salvia and basil leaves at night. Is there a safe control such as a powder, spray or oil that is effective at discouraging this pest?

search for the text
search for the slots concatenated
intersect

dealing with out-of-scope text

'''