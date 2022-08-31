# syntax=docker/dockerfile:1
# escape=\
# About
# Dockerfile for building Rasa chatbot
# More about the image - https://hub.docker.com/r/rasa/rasa/dockerfile

ARG VERSION=3.2.6-spacy-en
FROM rasa/rasa:$VERSION AS rasa

COPY . .

USER root
RUN ["pip", "install", "--upgrade", "-r", "requirements-update.txt"]
RUN ["python", "-m", "spacy", "download", "en_core_web_trf"]

ARG STREAM_READING_TIME_ENV=300
ARG SANIC_REQUEST_TIMEOUT=300
ARG REQUEST_TIMEOUT=300
ARG RESPONSE_TIMEOUT=300
ARG DEFAULT_STREAM_READING_TIMEOUT_IN_SECONDS=120

ENV STREAM_READING_TIME_ENV=300
ENV SANIC_REQUEST_TIMEOUT=300
ENV REQUEST_TIMEOUT=300
ENV RESPONSE_TIMEOUT=300
ENV DEFAULT_STREAM_READING_TIMEOUT_IN_SECONDS=120

# uncomment if model is not pushed
# RUN ["rasa", "train"]

USER 1001
EXPOSE 5005
ENTRYPOINT ["rasa", "run", "--request-timeout", "5000", "--cors", "*"]

# change shell
# SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# the entry point
# EXPOSE 5005
# ENTRYPOINT ["rasa"]
# CMD ["--help"]

# for development purposes, to attach to container, run the following:
# docker run -it --rm --entrypoint /bin/bash rasa/rasa:3.1.0-spacy-en
