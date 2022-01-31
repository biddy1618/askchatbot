# syntax=docker/dockerfile:1
# escape=\
# About

# FROM <image> (ARG <tag>)
# base image
ARG VERSION=3.0.2
FROM rasa/rasa-sdk:$VERSION AS rasa

USER root
RUN pip install --upgrade pandas==1.3.5

USER 1001
# ENTRYPOINT []