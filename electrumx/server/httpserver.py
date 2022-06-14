# Copyright (c) 2022 The Radiant Blockchain Developers
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

from functools import partial

try:
    import websockets
except ImportError:
    websockets = None

from aiorpcx.curio import spawn
from aiorpcx.session import RPCSession, SessionKind
from aiorpcx.util import NetAddress

from aiohttp import web

__all__ = ('serve_http', 'connect_http')


class HTTPTransport:
    '''Implementation of a http transport for session.py.'''

    def __init__(self, websocket, session_factory, kind):
        self.websocket = websocket
        self.kind = kind
        self.session = session_factory(self)
        self.closing = False

    @classmethod
    async def http_server(cls, session_factory, websocket, _path):
        transport = cls(websocket, session_factory, SessionKind.SERVER)
        await transport.process_messages()

    async def recv_message(self):
        message = await self.websocket.recv()
        # It might be nice to avoid the redundant conversions
        if isinstance(message, str):
            message = message.encode()
        self.session.data_received(message)
        return message

    async def process_messages(self):
        try:
            await self.session.process_messages(self.recv_message)
        except websockets.ConnectionClosed:
            pass

    # API exposed to session
    async def write(self, framed_message):
        # Prefer to send as text
        try:
            framed_message = framed_message.decode()
        except UnicodeDecodeError:
            pass
        await self.websocket.send(framed_message)

    async def close(self, _force_after=0):
        '''Close the connection and return when closed.'''
        self.closing = True
        await self.websocket.close()

    async def abort(self):
        '''Abort the connection.  For now this just calls close().'''
        self.closing = True
        await self.close()

    def is_closing(self):
        '''Return True if the connection is closing.'''
        return self.closing

    def proxy(self):
        return None

    def remote_address(self):
        result = self.websocket.remote_address
        if result:
            result = NetAddress(*result[:2])
        return result

def serve_http(session_factory, *args, **kwargs):
    http_handler = partial(HTTPTransport.http_server, session_factory)
    return websockets.serve(http_handler, *args, **kwargs)
