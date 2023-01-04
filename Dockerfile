# The Radiant Blockchain Developers
# The purpose of this image is to be able to host ElectrumX for radiantd (RADN)
# Build with: `docker build .`
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
#ENV SERVICES=tcp://0.0.0.0:50010,ws://0.0.0.0:50020,wss://0.0.0.0:50022
# NO SSL VERSION
ENV SERVICES=tcp://0.0.0.0:50010
ENV HOST=""
ENV ALLOW_ROOT=true
ENV CACHE_MB=300
ENV MAX_SEND=10000000
ENV MAX_RECV=10000000

EXPOSE 50010

ENTRYPOINT ["python3", "electrumx_server"]

##### DOCKER INFO
# build it with eg.: `docker build -t electrumx .`
# run it with eg.:
# `docker run -d --net=host -e DAEMON_URL="http://youruser:yourpass@localhost:7332" -e REPORT_SERVICES=tcp://example.com:50010 electrumx`
# for a proper clean shutdown, send TERM signal to the running container eg.: `docker kill --signal="TERM" CONTAINER_ID`
 
