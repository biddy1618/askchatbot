import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from typing import List, Tuple
from elasticsearch import RequestError

from actions.es import config

async def _cos_sim_query(query_vector: np.ndarray) -> dict:
    '''Exectute vector search in ES based on cosine similarity.

    Args:
        query_vector    (np.ndarray): Query vector.

    Returns:
        dict: Return hits.
    '''
    vector_name     = 'vectors.vector'
    source_nested   = {'includes': ['vectors.name', 'vectors.start', 'vectors.end']}

    cos     = f'cosineSimilarity(params.query_vector, "{vector_name}") + 1.0'
    script  = {"source": cos, "params": {"query_vector": query_vector}}

    source_query = {'includes': ['source', 'url', 'title', 'description', 'identification', 'development', 'damage', 'management', 'links']}

    path = vector_name.split('.')[0]
    query = {
        "bool": {
            "must": {"nested": {
                        "score_mode": "max" ,
                        "path"      : path  ,
                        "inner_hits": {"size": 3, "name": "nested", "_source": source_nested},
                        "query"     : {"function_score": {"script_score": {"script": script}}}}
            },
        }
    }

    response = await config.es_client.search(
        index   = config.es_combined_index  ,
        query   = query                     ,
        size    = config.es_search_size     ,
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
    query       : str               ,
    slots       : List[str] = None
    ) -> Tuple[list, str]:
    '''Perform search in ES base.

    Args:
        query       (str)       : Query statement.
        slots       (List[str]) : Additional entity queries. Defaults to None.

    Returns:
        Tuple[list, str]: Results from ES query and final transformed query that was embedded.
                            If slots were provided, then results with slots refinement.
    '''

    def _synonym_replace(text):
        tokens = config.tokenizer(text)
        text_modified = ""
        for token in tokens:
            t = token.text.lower()
                
            if t in config.synonym_dict:
                text_modified += config.synonym_dict[t]
                text_modified += token.whitespace_
            else:
                text_modified += token.text_with_ws

        return text_modified
    
    def _check_for_hardcoded_queries(text):
        
        tokens = config.tokenizer(text)
        text_modified = ""

        for token in tokens:
            if not token.is_stop:
                text_modified += token.text_with_ws
            
        query_vector = config.embed.encode([text_modified], show_progress_bar = False)[0]
        best_score  = 0
        best_result = None
        for h_query in config.hardcoded_queries:
            h_query_vector = h_query['vector']
            score = cosine_similarity([query_vector, h_query_vector])[0, 1]
            if score > best_score:
                best_score  = score
                best_result = h_query

        if best_score < 0.85:
            return None

        return best_result        
    
    check_hardcoded = _check_for_hardcoded_queries(query)
    
    query = _synonym_replace(query)

    if slots:
        query = '. '.join([query] + [_synonym_replace(s) for s in slots])

    # TF HUB model
    # query_vector = config.embed([query]).numpy()[0]

    # Sentence Encoder model
    query_vector = config.embed.encode([query], show_progress_bar = False)[0]
    
    hits = await _cos_sim_query(query_vector = query_vector)

    if check_hardcoded:
        urls = set([h['url'] for h in check_hardcoded['hits']])
        hits = [h for h in hits if h['url'] not in urls and h['_score'] > config.es_cut_off_hardcoded]
        hits = check_hardcoded['hits'] + hits

    return hits, query

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
        if h['source'] == 'askExtension': 
            h['_score'] *= config.es_ask_weight
    
    hits = [h for h in hits if len(h['url']) > 0]
    
    if filter:
        hits = [h for h in hits if h['_score'] > config.es_cut_off]
    
    hits = sorted(hits, key = lambda h: h['_score'], reverse = True)

    return hits

# Disable for the new view
# def _format_result(hit) -> dict:

#     score           = hit.get('_score'        , 0.0   )
#     source          = hit.get('source'        , None  )
#     url             = hit.get('url'           , None  )
#     title           = hit.get('title'         , None  )
#     description     = hit.get('description'   , None  )
#     identification  = hit.get('identification', None  )
#     development     = hit.get('development'   , None  )
#     damage          = hit.get('damage'        , None  )
#     management      = hit.get('management'    , None  )

#     def _format_scores(hit = None):
#         scores = hit['top_scores']
#         scores_dict = {}
        
#         for i, s in enumerate(scores):
#             s1 = {'score': s['score']}

#             name, index = s['source']['name'    ].split('_')
            
#             start       = s['source']['start'   ]
#             end         = s['source']['end'     ]
#             if end > config.es_field_limit:
#                 start   = config.es_field_limit - 50
#                 end     = config.es_field_limit
            
#             s1['field'] = name
            
#             if name == 'links': s1['text'] = hit['title'] + ' - ' + hit[name][int(index)]['title']
#             else:               s1['text'] = hit[name   ][start:end]
            
#             scores_dict['top_score_' + str(i+1)] = s1
        
#         return scores_dict

#     res = {}
#     if config.debug:
#         res['title'] = (
#             f'<p><em>{title}</em>'
#             f'</br>(score: {score:.2f})</br>'
#             f'(source: <a href="{url}" target="_blank">{source}</a>)</p>')
#     else:
#         res['title'] = (
#             f'<p><em>{title}</em>'
#             f'</br>(source: <a href="{url}" target="_blank">{source}</a>)</p>')
    
#     res['description'] = ''
#     if description:
#         res['description'] += (f'<p><strong>Details</strong>: {description[:100]}</p></br>'             )
#     if damage:
#         res['description'] += (f'<p><strong>Damage</strong>: {damage[:100]}</p></br>'                   )
#     if identification:
#         res['description'] += (f'<p><strong>Identification</strong>: {identification[:100]}</p></br>'   )
#     if development:
#         res['description'] += (f'<p><strong>Development</strong>: {development[:100]}</p></br>'         )
#     if management:
#         res['description'] += (f'<p><strong>Management</strong>: {management[:100]}</p></br>'           )
    
#     res['meta'  ] = {}
#     res['meta'  ]['url'   ] = url
#     res['meta'  ]['title' ] = title
#     res['meta'  ]['source'] = source
#     res['meta'  ]['scores'] = _format_scores(hit)
    
    
#     return res


# Enable for the new view
def _format_result(hit: dict) -> dict:
    '''Process formatted file single result for output.

    Args:
        hit (dict): Single result item.

    Returns:
        dict: Formatted result.
    '''
    
    score           = hit.get('_score'          , 0.0   )
    source          = hit.get('source'          , None  )
    url             = hit.get('url'             , None  )
    title           = hit.get('title'           , None  )
    description     = hit.get('description'     , None  )
    identification  = hit.get('identification'  , None  )
    development     = hit.get('development'     , None  )
    damage          = hit.get('damage'          , None  )
    management      = hit.get('management'      , None  )
    links           = hit.get('links'           , None  )
    
    def _format_images(links = None):
        images = []
        
        for l in links:
            if l['type'] == 'image':
                image = {
                    'src'   : l['src'  ],
                    'link'  : l['link' ],
                    'title' : l['title']
                }

                images.append(image)
        
        return images

    def _format_scores(hit = None):
        scores = hit['top_scores']

        scores_dict = {}
        for i, s in enumerate(scores):
            s1 = {'score': f'{s["score"]:.2f}'}

            if s['score'] < config.es_cut_off:
                break

            name, index = s['source']['name'].split('_')
            
            start       = s['source']['start'   ]
            end         = s['source']['end'     ]
            if end > config.es_field_limit:
                start   = config.es_field_limit - 50
                end     = config.es_field_limit

            s1['field'] = name
            
            if name == 'links':
                link = hit[name][int(index)]
                s1['text'   ] = hit['title'] + ' - ' + link['title']
                s1['src'    ] = link['link'] if len(link['link']) > 0  else link['src']
            else:
                s1['text'   ] = hit[name   ][start:end]
            
            scores_dict['top_score_' + str(i+1)] = s1
        
        return scores_dict

    res = {}
    
    res['source'] = source
    res['title' ] = title
    res['score' ] = f'{score:.2f}'
    res['cutoff'] = False
    res['url'   ] = url
    
    res['body'] = {}
    res['body']['description'   ] = description
    res['body']['identification'] = identification
    res['body']['development'   ] = development
    res['body']['damage'        ] = damage
    res['body']['management'    ] = management

    res['images'] = _format_images(links)
    res['scores'] = _format_scores(hit  )
    
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

async def submit(
    question    : str               ,
    slots       : List[str] = None
    ) -> Tuple[dict, str]:
    
    '''Perform ES query, transform results, print them, and return results.

    Args:
        question    (str)       : Question that is asked.
        slots       (List[str]) : Pest damage description. Defaults to None.
    
    Returns:
        Tuple[dict, str]: Results from ES query and final transformed query that was embedded.
                            If slots were provided, then results with slots refinement.
    '''

    hits, debug_query = await _handle_es_query(question, slots = slots)
    
    hits = _handle_es_result(hits)    
    
    res = _get_text(hits)
    
    return res, debug_query

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