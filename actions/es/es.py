import logging

from typing import List, Tuple

import numpy as np

from actions.es import config

logger = logging.getLogger(__name__)

async def _cos_sim_query(
    query_vector    : np.ndarray        ,
    filter_ids      : List[str] = None  ,
    ) -> dict:
    '''Exectute vector search in ES based on cosine similarity.

    Args:
        query_vector    (np.ndarray): Query vector.
        filter_ids      (List[str]) : Filter results based on the IDs given. Defaults to None.

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
            "filter"    : [],
            "must_not"  : []
        }
    }

    if filter_ids is not None:
        query['bool']['filter'].append({'ids': {'values': filter_ids     }})

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
    slots       : List[str] = None  ,
    filter_ids  : List[str] = None  ,
    ) -> list:
    '''Perform search in ES base.

    Args:
        query       (str)       : Query statement.
        slots       (List[str]) : Additional entity queries. Defaults to None.
        filter_ids  (List[str]) : IDs of docs that should be considered. Defaults to None.

    Returns:
        list: return list of hits. 
    '''    
    
    tokens = config.tokenizer(query)
    query_modified = ""
    replace = False
    for token in tokens:
        t = token.text.lower()
            
        if t in config.synonym_dict:
            query_modified += config.synonym_dict[t]
            query_modified += token.whitespace_
            replace = True
        else:
            query_modified += token.text_with_ws
        
    if not replace:
        query_modified = query

    # TF HUB model
    # query_vector = config.embed([query_modified]).numpy()[0]
    # if slots:
    #     slots_vector = np.average([config.embed([s]).numpy()[0] for s in slots] , axis = 0)
    #     query_vector = np.average(
    #         a       = [query_vector, slots_vector], 
    #         weights = [1 - config.es_slots_weight, config.es_slots_weight],
    #         axis    = 0
    #     )
    
    # Sentence Encoder model
    query_vector = config.embed.encode([query_modified], show_progress_bar = False)[0]
    if slots:
        slots_vector = np.average(
            [config.embed.encode([s], show_progress_bar = False)[0] for s in slots],
            axis = 0
        )
        query_vector = np.average(
            a       = [query_vector, slots_vector], 
            weights = [1 - config.es_slots_weight, config.es_slots_weight],
            axis    = 0
        )
    
    
    hits = await _cos_sim_query(
        query_vector    = query_vector,
        filter_ids      = filter_ids
    )

    return hits

def _handle_es_result(
    hits    : list,
    filter  : bool = True
    ) -> Tuple[list, list]:
    '''Process the ES query results (like filtering, reweighting, etc).

    Args:
        hits    (list): Results from ES query.
        filter  (bool): If cut off filter should be applied. Defaults to True.

    Returns:
        Tuple[list, list]: filtered and processed ES query results
    '''

    for h in hits: 
        if h['source'] == 'askExtension': 
            h['_score'] *= config.es_ask_weight
    
    hits = [h for h in hits if len(h['url']) > 0]
    
    if filter:
        hits = [h for h in hits if h['_score'] > config.es_cut_off]
    
    filter_ids = [h['_id'] for h in hits]
    hits = sorted(hits, key = lambda h: h['_score'], reverse = True)

    return hits, filter_ids

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
def _format_result(hit) -> dict:
    
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
    slots       : List[str] = None  ,
    filter_ids  : List[str] = None

    ) -> Tuple[dict, dict]:
    
    '''Perform ES query, transform results, print them, and return results.

    Args:
        question    (str)       : Question that is asked.
        slots       (List[str]) : Pest damage description. Defaults to None.
        filter_ids  (List[str]) : IDs of docs that should be considered. Defaults to None.
    
    Returns:
        Tuple[dict, dict]: Results from ES query. If slots were provided, then results with slots refinement.
    '''

    hits = await _handle_es_query(question, slots = slots, filter_ids = filter_ids)
    
    hits, filter_ids = _handle_es_result(hits)    
    
    res = _get_text(hits)
    
    return res, filter_ids
    