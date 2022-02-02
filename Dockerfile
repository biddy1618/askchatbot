# syntax=docker/dockerfile:1
# escape=\
# About
# Dockerfile for building Rasa chatbot
# More about the image - https://hub.docker.com/r/rasa/rasa/dockerfile

ARG VERSION=3.0.4-spacy-en
FROM rasa/rasa:$VERSION AS rasa

COPY . .

RUN ["rasa", "train"]
CMD ["run", "--cors", "*"]

# chage shell
# SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# the entry point
# EXPOSE 5005
# ENTRYPOINT ["rasa"]
# CMD ["--help"]