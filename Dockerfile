# The Radiant Blockchain Developers
# The purpose of this image is to be able to host ElectrumX for radiantd (RADN)
# Build with: `docker build .`
# Public images at: https://hub.docker.com/repository/docker/radiantblockchain
FROM ubuntu:20.04

LABEL maintainer="radiantblockchain@protonmail.com"
LABEL version="1.0.0"
LABEL description="Docker image for electrumx radiantd node"

ARG DEBIAN_FRONTEND=nointeractive
RUN apt update
RUN apt-get install -y curl
RUN curl -sL https://deb.nodesource.com/setup_12.x | bash -
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
 
# Install radiant-node
WORKDIR /root
RUN git clone --depth 1 --branch v1.0.0 https://github.com/radiantblockchain/electrumx.git
WORKDIR /root/electrumx

RUN python3 -m pip install aiorpcx
RUN python3 -m pip install pylru
RUN python3 -m pip install attr
RUN python3 -m pip install pycryptodome

EXPOSE 50010
 
ENTRYPOINT ["python3", "electrumx_server"]
  