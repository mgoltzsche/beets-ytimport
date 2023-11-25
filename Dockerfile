FROM ghcr.io/mgoltzsche/beets:0.3.0

# Install bats
USER root:root
RUN apk add --update --no-cache git bash
ARG BATS_VERSION=v1.8.2
RUN set -eux; \
	git clone -c 'advice.detachedHead=false' --depth=1 --branch=$BATS_VERSION https://github.com/bats-core/bats-core.git /tmp/bats; \
	/tmp/bats/install.sh /opt/bats; \
	ln -s /opt/bats/bin/bats /usr/local/bin/bats; \
	rm -rf /tmp/bats; \
	apk del git

# Install beets-ytimport from source
COPY dist /plugin/dist
RUN python -m pip install /plugin/dist/*
COPY example_beets_config.yaml /etc/beets/default-config.yaml
USER beets:beets
