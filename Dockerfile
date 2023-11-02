FROM ghcr.io/mgoltzsche/beets:0.3.0
COPY . /plugin
RUN python -m pip install /plugin/dist/*
COPY example_beets_config.yaml /etc/beets/default-config.yaml
