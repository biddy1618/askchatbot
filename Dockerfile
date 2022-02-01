# syntax=docker/dockerfile:1
# escape=\
# About

ARG VERSION=3.0.4-spacy-en
FROM rasa/rasa:$VERSION AS rasa

CMD ["run", "--cors", "*"]

# chage shell
# SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# the entry point
# EXPOSE 5005
# ENTRYPOINT ["rasa"]
# CMD ["--help"]