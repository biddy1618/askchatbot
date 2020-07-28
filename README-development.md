# Instructions to develop new skills for the chatbot

## Install the bot locally for development purposes

##### Install Ubuntu modules needed for local development

```bash
sudo apt-get update
sudo apt-get install curl python3-distutils build-essential

# check it is all there
gcc --version
g++ --version
```

##### Install Miniconda3 for Ubuntu

```bash
# download Miniconda installer for Python 3.7
# (https://docs.conda.io/en/latest/miniconda.html)
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh

# Install Miniconda
chmod +x Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh
Do you accept the license terms? [yes|no]
[no] >>> yes
.
Do you wish the installer to initialize Miniconda3
by running conda init? [yes|no]
[no] >>> yes

# Verify it works
$ source ~/.bashrc  # installer updated this, and will activate the base environment
(base) > conda --version
```

##### Create conda environments & install the bot for development

There are two 'bots'. One called `askchatbot` and one called `responseselectors`. 

You need to create a separate conda environment for each, and install the respective package in editable mode.

(TODO: make it possible to install it in a single environment)

###### Conda: `askchatbot`

```bash
conda create --name askchatbot python=3.7
conda activate askchatbot/askchatbot

git clone https://git.eduworks.us/ask-extension/askchatbot.git
cd askchatbot

# install the dependencies
pip install -r requirements-dev.txt

# install the askchatbot package in editable mode
pip install -e .
```

**WARNING:** 

The bot will not yet run on Windows, because it uses the `ConveRTTokenizer` in the NLU pipeline (see the `config.yml`). This tokenizer uses the python module `tensorflow-text` , which is not yet available on Windows. Check the [tensorflow-text github issue #44](https://github.com/tensorflow/text/issues/44) for the latest status.

Workarounds:

- Use WSL on windows
- Use docker-on-windows
- Use the `WhitespaceTokenizer` instead

###### Conda: responseselectors

```bash
conda create --name responseselectors python=3.7
conda activate responseselectors

git clone https://git.eduworks.us/ask-extension/askchatbot.git
cd askchatbot/responseselectors

# install the dependencies
pip install -r requirements-dev.txt

# install the responseselector package in editable mode
pip install -e .
```



## Pylint & black

The code is compliant with [pylint](https://pylint.readthedocs.io/en/latest/user_guide/installation.html), with some configurations adjusted to accept reformatting of [black](https://github.com/ambv/black)

A Pylint configuration file can be found in the top level directory:

```bash
<project-root>/.pylintrc
```

To black & pylint all python files in the project, run these commands:

```bash
# goto top level of project (where this README.md resides)
cd <project-root>  

# run black on all files
python -m black **/*.py

# run pylint as a module in your python environment:
# NOTE: running as a module bypasses the #! line inside the pylint script
python -m pylint -j 4 **/*.py  # use 4 cores to run pylint on all project code

# Alternatively, you can run the pylint script directly, but this is dangerous, because
# the pylint script will use the python command defined by the #! at the top.
# When this happens to point to a python version different than your anaconda or
# virtual env, you will get these type of errors:
#  E0401: Unable to import '---' (import-error)
pylint -j 4 **/*.py  # use 4 cores to run pylint on all project code

#################################################################################
# NOTE:                                                                         #
# When you run pylint with this projects' .pylintrc, sys.path is printed.       #
# This allows you to check that the correct python version is used.             #
# See init_hook in the .pylintrc file                                           # 
#################################################################################
```

### Line length

Linting is configured to accept a line length of 88 characters per line.

## Creating a 'release'

When a new version of the bot is shared with guest testers or customers, it is good to tag the master branch with a version number, using [semantic versioning](https://semver.org/).

This is the procedure to create an annotated tag in git:

```bash
git checkout dev                        # for now, we release from the dev branch
git pull                                # pull the latest
git tag -l                              # get a list of the tags
git tag -a 0.0.1 -m "Initial release"   # Define release tag
git show 0.0.1                          # to get details about this tag
git push origin dev --tags              # push all tags that are not already there

#########################################################
# In case you need to move the tag, use these commands: #
#########################################################
# Delete the tag on any remote before you push
git push origin :refs/tags/0.0.1
# Replace the tag to reference the most recent commit
git tag -fa 0.0.1
# Push the tag to the remote origin
git push origin dev --tags              # push all tags that are not already there

```



## To run the bot:

Go to the `askchatbot` directory, and train the model:

```bash
cd askchatbot/askchatbot
rasa train
```

Then, first set up your action server in one terminal window:
```bash
rasa run actions
```

Then, to talk to the bot from another terminal window:
```
rasa shell --debug
```

Note that `--debug` mode will produce a lot of output meant to help you understand how the bot is working 
under the hood. To simply talk to the bot, you can remove this flag.



## Testing the bot

Go to the `askchatbot` directory, and train the model:

```bash
cd askchatbot/askchatbot
rasa train
```

Then, run the tests:

```bash
rasa test
```

The results of the tests are written to the `askchatbot/askchatbot/results` folder:

- `confmat.png` - confusion matrix of the intent predictions
- `hist.png` - histogram of intent prediction confidence distribution
- `DIETClassifier_report.json` - precision, recall, f1-score, support for intent predictions by DIETClassifier
- `intent_report.json` - precision, recall, f1-score, confused_with, support for intent predictions by NLU




## Overview of the files

In the folder `askchatbot/askchatbot` you can find these files:

- Training data:
  - `data/nlu/*.md` - contains NLU training data in markdown format ([docs](https://rasa.com/docs/rasa/nlu/training-data-format/#markdown-format))
  - `data/core/*.md` - contains the dialog management training data (stories) in markdown format ([docs](https://rasa.com/docs/rasa/core/stories/#format))
  - `domain.yml` - the domain file, including bot response templates ([docs](https://rasa.com/docs/rasa/core/domains/))
- Custom actions:
  - `actions/actions_main.py` - contains custom action/api code ([docs](https://rasa.com/docs/rasa/core/actions/#custom-actions))
  - `actions/actions_config.py` - sets up default configuration for the bot at startup
  - `config.yml` - training configurations for the NLU pipeline ([docs](https://rasa.com/docs/rasa/nlu/choosing-a-pipeline/)) and dialog policies ([docs](https://rasa.com/docs/rasa/core/policies/))
  - `actions/bot_config.yml` - define configuration details here, including credentials for elastic search
  - `actions/cert.pem` - public ssl certificate of elastic search server, used by custom action
  - `actions/requirements-actions.txt` - the python dependencies for the custom actions

- Deployment:
  - `docker-compose.yml & Dockerfile` - to build the docker image of the action server
  - `credentials.yml` - credentials for the voice & chat platforms of the bot ([docs](https://rasa.com/docs/rasa/user-guide/messaging-and-voice-channels/))
  - `endpoints.yml` - the different endpoints the bot can use ([docs](https://rasa.com/docs/rasa/user-guide/configuring-http-api/#endpoint-configuration))
- Tests
  - `tests/*.md` - end-to-end test conversations in markdown format ([docs](https://rasa.com/docs/rasa/user-guide/testing-your-assistant/#end-to-end-testing))

