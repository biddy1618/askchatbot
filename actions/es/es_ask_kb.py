"""Functions to update ask_extension_kb index in elastic search and retrieve relevant data"""
from actions.es import config
from datetime import datetime 
import asyncio 
import requests 
from elasticsearch.helpers import async_bulk
import logging
logger = logging.getLogger(__name__)
import uvloop
# from threading import Thread
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def get_total_documents():
    resp = await config.es_client.cat.count('ask_extension_kb', params={"format": "json"})
    return int(resp[0]['count'])


async def update_kb(start, end):
    async def get_kb_items(url):
        s = requests.Session()
        with s.get(url, headers=None, stream=True) as resp:
            for item in resp.json():
                item['_index'] = 'ask_extension_kb'
                item['created_timestamp'] = datetime.strptime(item['created'].split()[0], '%Y-%m-%d').timestamp()
                item['updated_timestamp'] = datetime.strptime(item['created'].split()[0], '%Y-%m-%d').timestamp()
                yield item
    
    date = await retrieve_last_update()
    url = f"{config.os_ticket_url}{start}/{end}" if start and end else f"{config.os_ticket_url}{date}"
    await async_bulk(config.es_client, get_kb_items(url))

async def retrieve_last_update() -> str:
    """ Searches Elastic Search for last update to ask_extension_kb index. 

    Retruns:
        Last update date (string)
    """
    body = {
        'aggs': {
            'last_updated':{
                'max': {
                    'field': 'created_timestamp'
                }
            }
        }
    }
    res = await config.es_client.search(index='ask_extension_kb', body=body, size=0)
    timestamp = res['aggregations']['last_updated']['value']
    date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
    return date