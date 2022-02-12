import json

from es_connection import EsManagement
from mappings import ASKEXTENSION


es_connection = EsManagement()
es_connection.es_client.indices.delete(index = 'test', ignore = 404)
es_connection.create_index(index_name="test", mapping=ASKEXTENSION)
print(json.dumps(es_connection.es_client.indices.get_mapping(index="test"), indent=1))