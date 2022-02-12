from es_connection import EsManagement
import os

es_connection = EsManagement()

import constants
import pandas as pd

es_connection.populate_index(index_name="test", path=constants.ASKEXTENSION_FILE_RESULT)