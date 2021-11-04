# https://hub.docker.com/r/rasa/rasa-sdk/tags
FROM rasa/rasa-sdk:1.10.2

USER root
COPY requirements-actions.txt /app/actions

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/actions/requirements-actions.txt

COPY actions /app/actions

USER 1001
#CMD ["start", "--actions", "actions", "--debug"]
CMD ["start", "--actions", "actions"]
