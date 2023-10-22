FROM ghcr.io/mgoltzsche/beets:0.2.0
COPY . /plugin
RUN python -m pip install /plugin/dist/*
COPY example_beets_config.yaml /etc/beets/config.yaml
ENV BEETSDIR=/etc/beets

#USER root:root
#RUN apk add --update --no-cache git
#ARG YTMUSICAPI_VERSION=a252cd20b4f86f2fce1929146ea2aecab11570b8
#RUN python -m pip install git+https://github.com/mgoltzsche/ytmusicapi@${YTMUSICAPI_VERSION}
