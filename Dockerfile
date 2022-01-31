# syntax=docker/dockerfile:1
# escape=\
# About

# FROM <image> (ARG <tag>)
# base image
ARG VERSION=3.0.4-spacy-en
FROM rasa/rasa:$VERSION AS rasa

# RUN <command> (RUN ["executable", "param1", "param2"]) 
# run command and create new layer (`/bin/sh -c` for Linux), i.e. image build step
# 2 forms: exec (RUN ["sh", "-c", "echo", "$HOME"]) and shell (RUN sh -c echo $HOME)
# the latter one executes the $HOME in the shell mode (replace the variable)
# RUN sh -c mkdir $HOME/test - will create the folder under $HOME directory - shell form
# RUN ["sh", "-c", "mkdir", "$HOME/test"] - will show error due to invalid path $HOME/test - exec form
# default shell for ubuntu us `sh`
# difference between `/bash/sh` and `/bin/bash`: `bash` is superset of `sh` with more features and better syntax
# Shell is an interface between the user and the operating system, and sh implements the shell interface 
# $HOME is /root/ and RUN and CMD commands operate under root
# `bash -c` and `sh -c` expect a string as an argument
# RUN ["sh", "-c", "mkdir $HOME/test"]
# RUN sh -c "mkdir $HOME/test2"
# RUN bash -c "mkdir $HOME/test3"
# WORKDIR $HOME/test

# COPY ./requirements.txt ./requirements.txt
ENTRYPOINT []
# CMD ["pip list --format=freeze"]

# CMD ps -p $$;\
#     echo $0;\
#     echo sh HOME variable $HOME;\
#     bash -c "echo bash $HOME variable $HOME";\
#     ls $HOME/;\
#     sh -c "ls $HOME";\
#     bash -c "ls $HOME"

# CMD ["bash", "-c", "echo $HOME"]
# CMD ["bash", "-c", "ls $HOME"]

