"""This script allows use of an IDE (Wing, Pycharm, ...) to run the rasa shell:

(-) Place this script in root of Rasa bot project
(-) Open & run it from within your IDE

(-) In Wing, use External Console for better experience.
"""

import os
import sys

# insert path of this script in syspath so custom modules will be found
sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))

#
# This is exactly like issuing the command:
#  $ rasa shell --debug
#

#
sys.argv.append('shell')
#sys.argv.append('--model')
#sys.argv.append('/home/arjaan/rasa/bots/rasa-demo/rasa-demo/models/20191231-102143.tar.gz')
sys.argv.append('--enable-api')
sys.argv.append('--debug')

from rasa.__main__ import main
main()
