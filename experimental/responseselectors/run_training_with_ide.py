"""This script allows use of an IDE (Wing, Pycharm, ...) to train rasa:

(-) Place this script in same location as your actions.py
(-) Open & run it from within your IDE
"""

import os
import sys

# insert path of this script in syspath so custom modules will be found
sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))

#
# This is exactly like issuing the command:
#  $ rasa train --debug
#
sys.argv.append("train")
sys.argv.append("nlu")
sys.argv.append("--debug")
# sys.argv.append('--force')  # to force re-training even if data has not changed
# sys.argv.append('--dump-stories')
# sys.argv.append('--debug-plots')

if __name__ == "__main__":
    from rasa.__main__ import main

    main()
