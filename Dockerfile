# The Radiant Blockchain Developers
# The purpose of this image is to be able to host ElectrumX for radiantd (RXD)
# Build with: `docker build -t electrumx .`
# Public images at: https://hub.docker.com/repository/docker/radiantblockchain

FROM ubuntu:20.04

LABEL maintainer="radiantblockchain@protonmail.com"
LABEL version="1.2.0"
LABEL description="Docker image for electrumx radiantd node"

ARG DEBIAN_FRONTEND=nointeractive
RUN apt update
RUN apt-get install -y curl
RUN curl -sL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs

ENV PACKAGES="\
  build-essential \
  libcurl4-openssl-dev \
  software-properties-common \
  ubuntu-drivers-common \
  pkg-config \
  libtool \
  openssh-server \
  git \
  clinfo \
  autoconf \
  automake \
  vim \
  wget \
  cmake \
  python3 \
  python3-pip \
"
# Note can remove the opencl and ocl packages above when not building on a system for GPU/mining
# Included only for reference purposes if this container would be used for mining as well.

RUN apt update && apt install --no-install-recommends -y $PACKAGES  && \
    rm -rf /var/lib/apt/lists/* && \
    apt clean
 
# Create directory for DB
RUN mkdir /root/electrumdb

WORKDIR /root

# ORIGINAL SOURCE
RUN git clone --depth 1 --branch master https://github.com/radiantblockchain/electrumx.git

WORKDIR /root/electrumx

RUN python3 -m pip install -r requirements.txt

ENV DAEMON_URL=http://dockeruser:dockerpass@localhost:7332/
ENV COIN=Radiant
ENV REQUEST_TIMEOUT=60
ENV DB_DIRECTORY=/root/electrumdb
ENV DB_ENGINE=leveldb

# SSL VERSION
ENV SERVICES=tcp://0.0.0.0:50010,SSL://0.0.0.0:50012
ENV SSL_CERTFILE=/root/electrumdb/server.crt
ENV SSL_KEYFILE=/root/electrumdb/server.key
# NO SSL VERSION
#ENV SERVICES=tcp://0.0.0.0:50010
ENV HOST=""
ENV ALLOW_ROOT=true
ENV CACHE_MB=10000
ENV MAX_SESSIONS=10000
ENV MAX_SEND=10000000
ENV MAX_RECV=10000000

# Create SSL
WORKDIR /root/electrumdb
RUN openssl genrsa -out server.key 2048
RUN openssl req -new -key server.key -out server.csr -subj "/C=US/ST=Denial/L=Springfield/O=Dis/CN=radiantblockchain.org"
RUN openssl x509 -req -days 1825 -in server.csr -signkey server.key -out server.crt

EXPOSE 50010 50012

ENTRYPOINT ["python3", "electrumx_server"]

##### DOCKER INFO
# build it with eg.: `docker build -t electrumx .`
# run it with eg.:
# `docker run -d --net=host -e DAEMON_URL="http://youruser:yourpass@localhost:7332" -e REPORT_SERVICES=tcp://example.com:50010 electrumx`
# for a proper clean shutdown, send TERM signal to the running container eg.: `docker kill --signal="TERM" CONTAINER_ID`
 
