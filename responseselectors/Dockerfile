# https://hub.docker.com/r/rasa/rasa-sdk/tags
FROM rasa/rasa-sdk:1.10.2

COPY actions /app/actions

USER root
RUN apt-get update
RUN apt-get -y install curl python3-distutils build-essential
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/actions/requirements-actions.txt

USER 1001
#CMD ["start", "--actions", "actions", "--debug"]
CMD ["start", "--actions", "actions"]
