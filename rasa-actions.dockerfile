# syntax=docker/dockerfile:1
# escape=\
# About

# FROM <image> (ARG <tag>)
# base image
ARG VERSION=3.0.2
FROM rasa/rasa-sdk:$VERSION AS rasa-sdk

USER root
COPY ./actions/requirements-actions.txt /app/actions/requirements-actions.txt
RUN pip install --upgrade -r actions/requirements-actions.txt

USER 1001

# change shell
# SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# create a mount point for custom actions and the entry point
# WORKDIR /app
# EXPOSE 5055
# ENTRYPOINT ["./entrypoint.sh"]
# CMD ["start", "--actions", "actions"]