# https://hub.docker.com/r/rasa/rasa-sdk/tags
FROM rasa/rasa-sdk:1.10.0

COPY actions /app/actions
COPY ./credentials_elasticsearch.yml ./

USER root
RUN pip install --no-cache-dir -r /app/actions/requirements-actions.txt

USER 1001
CMD ["start", "--actions", "actions"]
