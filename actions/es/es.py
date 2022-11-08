import numpy as np

from typing import Tuple, List
from elasticsearch import RequestError
from actions.es import config

async def _cos_sim_query(query_vector: np.ndarray) -> dict:
    '''Exectute vector search in ES based on cosine similarity.

    Args:
        query_vector    (np.ndarray): Query vector.

    Returns:
        dict: Return hits.
    '''

    vector_name = 'vector'
    cos = f'cosineSimilarity(params.query_vector, "{vector_name}") + 1.0'
    source_query = {'exclude': 'vector'} # only vector field not returned
    collapse_field = {'field': 'url'} # Returns only unique URLs

    script_query = {
        "script_score": {
            "query": {"match_all": {}},
            "script": {"source": cos, "params": {"query_vector": query_vector}
            }
        }
    }

    response = await config.es_client.search(
        index    = config.es_combined_index  ,
        query    = script_query              ,
        size     = config.es_search_size     ,
        collapse = collapse_field            ,
        _source  = source_query
    )

    hits = [{'score': hit['_score'] - 1, **hit['_source']} for hit in response['hits']['hits']]
    return hits


async def _handle_es_query(query: str) -> list:
    '''Perform search in ES base.

    Args:
        query       (str)       : Query statement.
        slots       (List[str]) : Additional entity queries. Defaults to None.

    Returns:
        list: Results from ES query.
    '''    
    
    # TF HUB model
    # query_vector = config.embed([query]).numpy()[0]

    # Sentence Encoder model
    query_vector = config.embed.encode([query], show_progress_bar = False)[0]
    
    hits = await _cos_sim_query(query_vector = query_vector)

    return hits

def _handle_es_result(
    hits    : list,
    filter  : bool = True
    ) -> list:
    '''Process the ES query results (like filtering, reweighting, etc).

    Args:
        hits    (list): Results from ES query.
        filter  (bool): If cut off filter should be applied. Defaults to True.

    Returns:
        list: filtered and processed ES query results
    '''

    for h in hits: 
        if h['source'] != config.client: 
            h['score'] *= config.es_downweight
    
    hits = [h for h in hits if len(h['url']) > 0]
    
    if filter:
        hits = [h for h in hits if h['score'] > config.es_cut_off]
    
    hits = sorted(hits, key = lambda h: h['score'], reverse = True)

    return hits


# Enable for the new view
def _format_result(hit: dict) -> dict:
    '''Process formatted file single result for output.

    Args:
        hit (dict): Single result item.

    Returns:
        dict: Formatted result.
    '''
    
    score       = hit.get('score'       , 0.0                       )
    source      = hit.get('source'      , 'placeholder_source'      )
    url         = hit.get('url'         , 'placeholder_url'         )
    title       = hit.get('title'       , 'placeholder_title'       )
    subHead     = hit.get('subHead'     , 'placeholder_subHead'     )
    text        = hit.get('text'        , 'placeholder_text'        )
    thumbnail   = hit.get('thumbnail'   , 'placeholder_thumbnail'   )
    
    res = {}
    
    res['source'] = source
    res['title' ] = title
    res['score' ] = f'{score:.2f}'
    res['cutoff'] = False
    res['url'   ] = url
    
    res['subHead'   ] = subHead
    res['text'      ] = text
    res['thumbnail' ] = thumbnail
    
    return res

def _get_text(hits: list) -> dict:
    '''Process results for output.

    Args:
        hits (list): Sorted results from ES query.
        
    Returns:
        dict: Data for chatbot to return.
    '''

    top_n = config.es_top_n
    if len(hits) < config.es_top_n:
        top_n = len(hits)

    res = {
        'text'      : 'Here are my top results:',
        # 'payload'   : 'collapsible',
        'payload'   : 'resultscollapsible',
        'data'      : []
    }

    if len(hits):
        for h in hits[:top_n]: res['data'].append(_format_result(h))   
    
    return res

async def submit(question: str, slots: List[str] = None) -> Tuple[dict, str]:
    
    '''Perform ES query, transform results, print them, and return results.

    Args:
        question    (str)       : Question that is asked.
    
    Returns:
        dict: Results from ES query.
    '''

    hits = await _handle_es_query(question)
    
    hits = _handle_es_result(hits)    
    
    res = _get_text(hits)
    
    return res, question

async def save_chat_logs(
    chat_export: dict
    ) -> None:
    '''Save the chat into the index logs in ES.

    Args:
        chat_export (dict): The chat export object containing chat history for particular session.
    '''
    try:
        response = await config.es_client.index(
            index       = config.es_logging_index   ,
            document    = chat_export               ,
            id          = chat_export['chat_id']    ,
        )
    except RequestError as e:
        raise(e)
    
    try:
        assert response['result'] in ['created', 'updated']
    except AssertionError as e:
        raise e