#!/bin/sh
# Install python3 package manager pip to begin install deps
#
# sudo apt install python3-pip
#
# Install deps:
# 
# python3 -m pip install aiorpcx
# python3 -m pip install aiohttp
# python3 -m pip install pylru
# python3 -m pip install pycryptodome
# python3 -m pip install websockets

export DAEMON_URL=http://raduser:radpass@localhost:7332/
export COIN=Radiant
export REQUEST_TIMEOUT=60
export DB_DIRECTORY=/Users/username/git/electrumdb
export DB_ENGINE=leveldb
export SERVICES=tcp://0.0.0.0:50010,ws://0.0.0.0:50020 #,wss://0.0.0.0:50022
export HOST=""
export ALLOW_ROOT=true
export CACHE_MB=300
export MAX_SEND=7000000
export MAX_RECV=7000000
# Following might be needed on newer OSX 12.0 versions
# export LIBRARY_PATH="$LIBRARY_PATH:$(brew --prefix)/lib"
# export CPATH="$CPATH:$(brew --prefix)/include"

python electrumx_server

