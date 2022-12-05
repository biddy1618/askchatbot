FROM condaforge/mambaforge:latest

WORKDIR /app

ARG CI_COMMIT_BRANCH
ENV CI_COMMIT_BRANCH=$CI_COMMIT_BRANCH


COPY ./actions /app/actions
COPY environment_rasa_actions.yml /app/environment_rasa_actions.yml
RUN mamba env create -f environment_rasa_actions.yml 

SHELL ["conda", "run", "-n", "rasa_actions_env", "/bin/bash", "-c"]


ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "rasa_actions_env", "python",  "-m", "rasa", "run", "actions", "--cors", "*"]
