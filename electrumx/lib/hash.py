# This license can be used by developers, projects or companies who wish to make their software or applications available for open (free) usage only on the Radiant Blockchains.
# 
# Copyright (c) 2022 The Radiant Blockchain Developers
# 
# Open Radiant Blockchain (RAD) License Version 1
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#  
# 1 - The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# 2 - The Software, and any software that is derived from the Software or parts thereof,
# can only be used on the Radiant (RAD) blockchains. The Radiant (RAD) blockchains are defined,
# for purposes of this license, as the Radiant (RAD) blockchains containing block height #10,459
# with the hash "0000000000229980bb7bcf653ebb94d6ffe18fed6cd3a3a98b876312414cb831" and that 
# contains the longest persistent chain of blocks accepted by this Software, as well as the test 
# blockchains that contain the longest persistent chains of blocks accepted by this Software.
# 
# 3 - The Software, and any software that is derived from the Software or parts thereof, can only
# be used on Radiant (RAD) blockchain that maintains the original difficulty adjustment algorithm, 
# maintains the block subsidy emission rate defined in the original version of this Software, and 
# ensures all coins are spendable in the normal manner without either subverting, undermining, 
# changing, diminishing, nullifying, hijacking, or altering the way existing coins can be spent. Any 
# attempt or proposal by an entity to violate, change, or remove the logic for verifying 
# digital chains of signatures for existing coins will be deemed a violation of this license 
# and that entity must cease to use the Software immediately.
# 
# 4 - Users and providers of the Software agree to insure themselves against any loss of any kind
# if they wish to mitigate the effects of theft or error. The Users and providers agree
# and understand that under no circumstances will there be recourse through Radiant (RAD) blockchain
# providers via subverting, undermining, changing, diminishing, nullifying, hijacking, or altering 
# the way existing coins can be spent and the proper functioning of the verification of chains of 
# digital signatures.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

# Previous version of the software are copyright and licensed as follows:

# Copyright (c) 2016-2017, Neil Booth
# Copyright (c) 2017, the ElectrumX authors
#
# All rights reserved.
#
# The MIT License (MIT)
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# and warranty status of this software.


'''Cryptograph hash functions and related classes.'''


import hashlib
import hmac

from electrumx.lib.util import bytes_to_int, int_to_bytes, hex_to_bytes
from Crypto.Hash import SHA512
_sha256 = hashlib.sha256
_new_hash = hashlib.new
_new_hmac = hmac.new
HASHX_LEN = 11


def sha256(x):
    '''Simple wrapper of hashlib sha256.'''
    return _sha256(x).digest()


def ripemd160(x):
    '''Simple wrapper of hashlib ripemd160.'''
    h = _new_hash('ripemd160')
    h.update(x)
    return h.digest()


def double_sha256(x):
    '''SHA-256 of SHA-256, as used extensively in bitcoin.'''
    return sha256(sha256(x))

def double_sha512_256(x):
    '''SHA-512/256 of SHA-512/256, as used extensively in radiant.'''
    h = SHA512.new(truncate="256")
    h.update(x)
    dh = SHA512.new(truncate="256")
    dh.update(h.digest())
    return dh.digest()

def hash_to_hex_str(x):
    '''Convert a big-endian binary hash to displayed hex string.

    Display form of a binary hash is reversed and converted to hex.
    '''
    return bytes(reversed(x)).hex()


def hex_str_to_hash(x):
    '''Convert a displayed hex string to a binary hash.'''
    return bytes(reversed(hex_to_bytes(x)))


class Base58Error(Exception):
    '''Exception used for Base58 errors.'''


class Base58(object):
    '''Class providing base 58 functionality.'''

    chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    assert len(chars) == 58
    cmap = {c: n for n, c in enumerate(chars)}

    @staticmethod
    def char_value(c):
        val = Base58.cmap.get(c)
        if val is None:
            raise Base58Error('invalid base 58 character "{}"'.format(c))
        return val

    @staticmethod
    def decode(txt):
        """Decodes txt into a big-endian bytearray."""
        if not isinstance(txt, str):
            raise TypeError('a string is required')

        if not txt:
            raise Base58Error('string cannot be empty')

        value = 0
        for c in txt:
            value = value * 58 + Base58.char_value(c)

        result = int_to_bytes(value)

        # Prepend leading zero bytes if necessary
        count = 0
        for c in txt:
            if c != '1':
                break
            count += 1
        if count:
            result = bytes(count) + result

        return result

    @staticmethod
    def encode(be_bytes):
        """Converts a big-endian bytearray into a base58 string."""
        value = bytes_to_int(be_bytes)

        txt = ''
        while value:
            value, mod = divmod(value, 58)
            txt += Base58.chars[mod]

        for byte in be_bytes:
            if byte != 0:
                break
            txt += '1'

        return txt[::-1]

    @staticmethod
    def decode_check(txt, *, hash_fn=double_sha256):
        '''Decodes a Base58Check-encoded string to a payload.  The version
        prefixes it.'''
        be_bytes = Base58.decode(txt)
        result, check = be_bytes[:-4], be_bytes[-4:]
        if check != hash_fn(result)[:4]:
            raise Base58Error('invalid base 58 checksum for {}'.format(txt))
        return result

    @staticmethod
    def encode_check(payload, *, hash_fn=double_sha256):
        """Encodes a payload bytearray (which includes the version byte(s))
        into a Base58Check string."""
        be_bytes = payload + hash_fn(payload)[:4]
        return Base58.encode(be_bytes)
