# syntax=docker/dockerfile:1
# escape=\
# About
# Dockerfile for building Rasa chatbot
# More about the image - https://hub.docker.com/r/rasa/rasa/dockerfile

ARG VERSION=3.1.0-spacy-en
FROM rasa/rasa:$VERSION AS rasa

COPY . .

USER root
RUN ["pip", "install", "--upgrade", "-r", "requirements-update.txt"]
RUN ["python", "-m", "spacy", "download", "en_core_web_trf"]
RUN ["rasa", "train"]

USER 1001
CMD ["run", "--cors", "*"]

# change shell
# SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# the entry point
# EXPOSE 5005
# ENTRYPOINT ["rasa"]
# CMD ["--help"]

# for development purposes, to attach to container, run the following:
# docker run -it --rm --entrypoint /bin/bash rasa/rasa:3.1.0-spacy-en