import os
from pathlib import Path

_PATH = Path(__file__).parents[1].as_posix()

PATH_DATA_ASKEXTENSION  = _PATH + '/data/askextension/2020-08-20/'
PATH_DATA_UCIPM         = _PATH + '/data/uc_ipmdata/updated/'
PATH_DATA_RESULTS       = _PATH + '/data/transformed/'

if not os.path.exists(PATH_DATA_RESULTS):
    os.makedirs(PATH_DATA_RESULTS)

ASKEXTENSION_FILE_NAMES = [PATH_DATA_ASKEXTENSION + f   for f in os.listdir(PATH_DATA_ASKEXTENSION)]
UCIPM_FILE_NAMES        = [PATH_DATA_UCIPM + f          for f in os.listdir(PATH_DATA_UCIPM)]

ASKEXTENSION_FILE_RESULT = PATH_DATA_RESULTS + 'askextension_transformed.json'

ASKEXTENSION_QUESTION_URL = 'https://ask2.extension.org/kb/faq.php?id='