# syntax=docker/dockerfile:1
# escape=\
# About
# Dockerfile for building Rasa Actions server
# More about the image - https://hub.docker.com/r/rasa/rasa-sdk/dockerfile

# FROM <image> (ARG <tag>)
# base image
ARG VERSION=3.2.0
FROM rasa/rasa-sdk:$VERSION AS rasa-sdk


USER root

RUN apt-get update -qq && \
    apt-get install -y python3-tk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
    
COPY ./actions /app/actions

RUN pip install --upgrade -r actions/requirements-update.txt

ENV STREAM_READING_TIME_ENV=300
ENV SANIC_REQUEST_TIMEOUT=300
ENV REQUEST_TIMEOUT=300
ENV RESPONSE_TIMEOUT=300
ENV DEFAULT_STREAM_READING_TIMEOUT_IN_SECONDS=120


USER 1001

# change shell
# SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# create a mount point for custom actions and the entry point
# WORKDIR /app
# EXPOSE 5055
# ENTRYPOINT ["./entrypoint.sh"]
# CMD ["start", "--actions", "actions"]

# for development purposes, to attach to container, run the following:
# docker run -it --rm --entrypoint /bin/bash rasa/rasa-sdk:3.1.1