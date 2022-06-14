===================================================================================
ElectrumX - Reimplementation of electrum-server for Radiant Blockchain (RXD) 
===================================================================================

https://radiantblockchain.org

Digital Ownership Revolution.

  :Licence: Radiant MIT
  :Language: Python (>= 3.8)
  :Author: The Radiant Blockchain Developers

Documentation
=============

See `readthedocs <https://electrumx.readthedocs.io/>`_.

Misc Troubleshooting
==============

Problems on OSX 12.0+
Errors like:

```
...
 plyvel/_plyvel.cpp:703:10: fatal error: 'leveldb/db.h' file not found
      #include "leveldb/db.h"
               ^~~~~~~~~~~~~~

```

See: https://github.com/wbolster/plyvel/issues/100

```
export LIBRARY_PATH="$LIBRARY_PATH:$(brew --prefix)/lib"
export CPATH="$CPATH:$(brew --prefix)/include"

// Now install requirements
pip install -r requirements.txt 

Install for websockets support: 
// python3 -m pip install websockets

```