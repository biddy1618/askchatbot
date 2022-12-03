FROM condaforge/mambaforge:latest

USER root 

COPY . .
RUN mamba env create -f environment_rasa.yml 

SHELL ["conda", "run", "-n", "rasa_env", "/bin/bash", "-c"]

ARG BRANCH
ENV BRANCH=$BRANCH

RUN  ["conda", "run", "--no-capture-output", "-n", "rasa_env", "python",  "-m", "spacy", "download", "en_core_web_trf"]
# uncomment if model is not pushed
#  RUN  ["conda", "run", "--no-capture-output", "-n", "rasa_actions_env", "python", "-m", "rasa", "train"]

USER 1001
EXPOSE 5005
ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "rasa_env", "python",  "-m", "rasa", "run", "--request-timeout", "3500", "--cors", "*"]
