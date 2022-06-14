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

'''Transaction-related classes and functions.'''

from collections import namedtuple

from electrumx.lib.hash import double_sha256, hash_to_hex_str, sha256
from electrumx.lib.util import (
    unpack_le_int32_from, unpack_le_int64_from, unpack_le_uint16_from,
    unpack_be_uint16_from,
    unpack_le_uint32_from, unpack_le_uint64_from, pack_le_int32, pack_varint,
    pack_le_uint32, pack_le_int64, pack_varbytes, pack_le_uint64
)
from electrumx.lib.script import Script
ZERO = bytes(32)
MINUS_1 = 4294967295


class Tx(namedtuple("Tx", "version inputs outputs locktime")):
    '''Class representing a transaction.'''

    def serialize(self):
        return b''.join((
            pack_le_int32(self.version),
            pack_varint(len(self.inputs)),
            b''.join(tx_in.serialize() for tx_in in self.inputs),
            pack_varint(len(self.outputs)),
            b''.join(tx_out.serialize() for tx_out in self.outputs),
            pack_le_uint32(self.locktime)
        ))


class TxInput(namedtuple("TxInput", "prev_hash prev_idx script sequence")):
    '''Class representing a transaction input.'''
    def __str__(self):
        script = self.script.hex()
        prev_hash = hash_to_hex_str(self.prev_hash)
        return ("Input({}, {:d}, script={}, sequence={:d})"
                .format(prev_hash, self.prev_idx, script, self.sequence))

    def is_generation(self):
        '''Test if an input is generation/coinbase like'''
        return self.prev_idx == MINUS_1 and self.prev_hash == ZERO

    def serialize(self):
        return b''.join((
            self.prev_hash,
            pack_le_uint32(self.prev_idx),
            pack_varbytes(self.script),
            pack_le_uint32(self.sequence),
        ))


class TxOutput(namedtuple("TxOutput", "value pk_script")):

    def serialize(self):
        return b''.join((
            pack_le_int64(self.value),
            pack_varbytes(self.pk_script),
        ))


class Deserializer(object):
    '''Deserializes blocks into transactions.

    External entry points are read_tx(), read_tx_and_hash(),
    read_tx_and_vsize() and read_block().

    This code is performance sensitive as it is executed 100s of
    millions of times during sync.
    '''

    def __init__(self, binary, start=0):
        assert isinstance(binary, bytes)
        self.binary = binary
        self.binary_length = len(binary)
        self.cursor = start

    def read_tx(self):
        '''Return a deserialized transaction.'''
        return Tx(
            self._read_le_int32(),  # version
            self._read_inputs(),    # inputs
            self._read_outputs(),   # outputs
            self._read_le_uint32()  # locktime
        )

    def read_tx_and_hash(self):
        '''Return a (deserialized TX, tx_hash) pair.

        The hash needs to be reversed for human display; for efficiency
        we process it in the natural serialized order.
        '''
        start = self.cursor
        the_tx = self.read_tx()
        # If the transaction is version 3, then we use the alternative txid generation scheme
        if the_tx.version == 3:
            return the_tx, self.get_transaction_hash_preimage_v3(the_tx)
        else:
            return the_tx, double_sha256(self.binary[start:self.cursor])

    # Get the double_sha256 of the transaction preimage used for generating the new txid
    # The benefits of using version 3 is we can do compressed induction proofs
    def get_transaction_hash_preimage_v3(self, tx):
        hashPrevInputs = self.get_hash_prev_inputs(tx)
        hashSequence = self.get_hash_sequence(tx)
        hashOutputHashes = self.get_hash_output_hashes(tx)
        preimage = b''.join((
            pack_le_uint32(tx.version),
            pack_le_int32(len(tx.inputs)),
            hashPrevInputs,
            hashSequence,
            pack_le_int32(len(tx.outputs)),
            hashOutputHashes,
            pack_le_uint32(tx.locktime)
        ))
        h = double_sha256(preimage)
        print("v3 txid: {}".format(h.hex()))
        print("v3 pre: {}".format(preimage.hex()))
        return h

 
    def get_hash_prev_inputs(self, tx):
        inputs = b''
        for txin in tx.inputs:
            inputs = b''.join((
                inputs,
                txin.prev_hash,
                pack_le_uint32(txin.prev_idx),
                double_sha256(txin.script)
            ))
        h = double_sha256(inputs)
        return h
 
    def get_hash_sequence(self, tx):
        inputs = b''
        for txin in tx.inputs:
            inputs = b''.join((
                inputs,
                pack_le_uint32(txin.sequence)
            ))
        h = double_sha256(inputs)
        return h

    # Generate the hash of the output hashes
    def calculate_pushrefs_count_and_hash(self, pk_script):
        outputs = b''
        zeroRef = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
        push_input_refs = Script.get_push_input_refs(pk_script)
        if len(push_input_refs) > 0:
            push_input_refs_hash = double_sha256(b''.join(sorted(push_input_refs)))
        else:
            push_input_refs_hash = zeroRef
        
        result = b''.join((pack_le_uint32(len(push_input_refs) ), push_input_refs_hash))
        return result

    # Generate the hash of the output hashes
    def get_hash_output_hashes(self, tx):
        outputs = b''
        for txout in tx.outputs:
            outputs = b''.join((
                outputs,
                pack_le_uint64(txout.value),
                double_sha256(txout.pk_script),
                self.calculate_pushrefs_count_and_hash(txout.pk_script),
            ))
        h = double_sha256(outputs)
        return h

    def read_tx_and_vsize(self):
        '''Return a (deserialized TX, vsize) pair.'''
        return self.read_tx(), self.binary_length

    def read_tx_block(self):
        '''Returns a list of (deserialized_tx, tx_hash) pairs.'''
        read = self.read_tx_and_hash
        # Some coins have excess data beyond the end of the transactions
        return [read() for _ in range(self._read_varint())]

    def _read_inputs(self):
        read_input = self._read_input
        return [read_input() for i in range(self._read_varint())]

    def _read_input(self):
        return TxInput(
            self._read_nbytes(32),   # prev_hash
            self._read_le_uint32(),  # prev_idx
            self._read_varbytes(),   # script
            self._read_le_uint32()   # sequence
        )

    def _read_outputs(self):
        read_output = self._read_output
        return [read_output() for i in range(self._read_varint())]

    def _read_output(self):
        return TxOutput(
            self._read_le_int64(),  # value
            self._read_varbytes(),  # pk_script
        )

    def _read_byte(self):
        cursor = self.cursor
        self.cursor += 1
        return self.binary[cursor]

    def _read_nbytes(self, n):
        cursor = self.cursor
        self.cursor = end = cursor + n
        assert self.binary_length >= end
        return self.binary[cursor:end]

    def _read_varbytes(self):
        return self._read_nbytes(self._read_varint())

    def _read_varint(self):
        n = self.binary[self.cursor]
        self.cursor += 1
        if n < 253:
            return n
        if n == 253:
            return self._read_le_uint16()
        if n == 254:
            return self._read_le_uint32()
        return self._read_le_uint64()

    def _read_le_int32(self):
        result, = unpack_le_int32_from(self.binary, self.cursor)
        self.cursor += 4
        return result

    def _read_le_int64(self):
        result, = unpack_le_int64_from(self.binary, self.cursor)
        self.cursor += 8
        return result

    def _read_le_uint16(self):
        result, = unpack_le_uint16_from(self.binary, self.cursor)
        self.cursor += 2
        return result

    def _read_be_uint16(self):
        result, = unpack_be_uint16_from(self.binary, self.cursor)
        self.cursor += 2
        return result

    def _read_le_uint32(self):
        result, = unpack_le_uint32_from(self.binary, self.cursor)
        self.cursor += 4
        return result

    def _read_le_uint64(self):
        result, = unpack_le_uint64_from(self.binary, self.cursor)
        self.cursor += 8
        return result
