"""
Copyright (c) 2012-2019 Roger Light and others

All rights reserved. This program and the accompanying materials
are made available under the terms of the Eclipse Public License v2.0
and Eclipse Distribution License v1.0 which accompany this distribution.

The Eclipse Public License is available at
    http://www.eclipse.org/legal/epl-v10.html
and the Eclipse Distribution License is available at
    http://www.eclipse.org/org/documents/edl-v10.php.

Contributors:
    Roger Light - initial API and implementation
    Ian Craggs - MQTT V5 support
"""

import os
import struct
import base64
import hashlib
import uuid


class WebsocketConnectionError(ValueError):
    """
    WebsocketConnectionError class.
    """


class WebsocketWrapper:
    """
    WebsocketWrapper class.
    """

    OPCODE_CONTINUATION = 0x0
    OPCODE_TEXT = 0x1
    OPCODE_BINARY = 0x2
    OPCODE_CONNCLOSE = 0x8
    OPCODE_PING = 0x9
    OPCODE_PONG = 0xA

    def __init__(self, socket, host, port, is_ssl, path, extra_headers):
        """
        Constructor.
        """

        self.connected = False

        self._ssl = is_ssl
        self._host = host
        self._port = port
        self._socket = socket
        self._path = path

        self._sendbuffer = bytearray()
        self._readbuffer = bytearray()

        self._requested_size = 0
        self._payload_head = 0
        self._readbuffer_head = 0

        self._do_handshake(extra_headers)

    def __del__(self):
        """
        Nullify send and read buffers.
        """

        self._sendbuffer = None
        self._readbuffer = None

    def _do_handshake(self, extra_headers):
        """
        Do handshake.
        """

        sec_websocket_key = uuid.uuid4().bytes
        sec_websocket_key = base64.b64encode(sec_websocket_key)

        websocket_headers = {
            "Host": "{self._host:s}:{self._port:d}".format(self=self),
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Origin": "https://{self._host:s}:{self._port:d}".format(self=self),
            "Sec-WebSocket-Key": sec_websocket_key.decode("utf8"),
            "Sec-Websocket-Version": "13",
            "Sec-Websocket-Protocol": "mqtt",
        }

        # This is checked in ws_set_options so it will either be None, a
        # dictionary, or a callable
        if isinstance(extra_headers, dict):
            websocket_headers.update(extra_headers)
        elif callable(extra_headers):
            websocket_headers = extra_headers(websocket_headers)

        parms = "\r\n".join(f"{i}: {j}" for i, j in websocket_headers.items())
        header = (f"GET {self._path} HTTP/1.1\r\n{parms}\r\n\r\n").encode("utf8")
        self._socket.send(header)

        has_secret = False
        has_upgrade = False

        while True:
            # read HTTP response header as lines
            byte = self._socket.recv(1)

            self._readbuffer.extend(byte)

            # line end
            if byte == b"\n":
                if len(self._readbuffer) > 2:
                    # check upgrade
                    if b"connection" in str(self._readbuffer).lower().encode("utf-8"):
                        if b"upgrade" not in str(self._readbuffer).lower().encode(
                            "utf-8"
                        ):
                            raise WebsocketConnectionError(
                                "WebSocket handshake error, connection not upgraded"
                            )
                        has_upgrade = True

                    # check key hash
                    if b"sec-websocket-accept" in str(self._readbuffer).lower().encode(
                        "utf-8"
                    ):
                        GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

                        server_hash = self._readbuffer.decode("utf-8").split(": ", 1)[1]
                        server_hash = server_hash.strip().encode("utf-8")

                        client_hash = sec_websocket_key.decode("utf-8") + GUID
                        client_hash = hashlib.sha1(client_hash.encode("utf-8"))
                        client_hash = base64.b64encode(client_hash.digest())

                        if server_hash != client_hash:
                            raise WebsocketConnectionError(
                                "WebSocket handshake error, invalid secret key"
                            )
                        has_secret = True
                else:
                    # ending linebreak
                    break

                # reset linebuffer
                self._readbuffer = bytearray()

            # connection reset
            elif not byte:
                raise WebsocketConnectionError("WebSocket handshake error")

        if not has_upgrade or not has_secret:
            raise WebsocketConnectionError("WebSocket handshake error")

        self._readbuffer = bytearray()
        self.connected = True

    def _create_frame(self, opcode, data, do_masking=1):
        """
        Create frame.
        """

        header = bytearray()
        length = len(data)

        mask_key = bytearray(os.urandom(4))
        mask_flag = do_masking

        # 1 << 7 is the final flag, we don't send continuated data
        header.append(1 << 7 | opcode)

        if length < 126:
            header.append(mask_flag << 7 | length)

        elif length < 65536:
            header.append(mask_flag << 7 | 126)
            header += struct.pack("!H", length)

        elif length < 0x8000000000000001:
            header.append(mask_flag << 7 | 127)
            header += struct.pack("!Q", length)

        else:
            raise ValueError("Maximum payload size is 2^63")

        if mask_flag == 1:
            for index in range(length):
                data[index] ^= mask_key[index % 4]
            data = mask_key + data

        return header + data

    def _buffered_read(self, length):
        """
        Buffered read.
        """

        # try to recv and store needed bytes
        wanted_bytes = length - (len(self._readbuffer) - self._readbuffer_head)
        if wanted_bytes > 0:
            data = self._socket.recv(wanted_bytes)

            if not data:
                raise ConnectionAbortedError
            self._readbuffer.extend(data)

            if len(data) < wanted_bytes:
                raise BlockingIOError

        self._readbuffer_head += length
        return self._readbuffer[self._readbuffer_head - length : self._readbuffer_head]

    def _recv_impl(self, length):
        """
        Receive impl.

        Try to decode websocket payload part from data.
        """

        try:
            self._readbuffer_head = 0

            result = None

            chunk_startindex = self._payload_head
            chunk_endindex = self._payload_head + length

            header1 = self._buffered_read(1)
            header2 = self._buffered_read(1)

            opcode = header1[0] & 0x0F
            maskbit = header2[0] & 0x80 == 0x80
            lengthbits = header2[0] & 0x7F
            payload_length = lengthbits
            mask_key = None

            # read length
            if lengthbits == 0x7E:
                value = self._buffered_read(2)
                (payload_length,) = struct.unpack("!H", value)

            elif lengthbits == 0x7F:
                value = self._buffered_read(8)
                (payload_length,) = struct.unpack("!Q", value)

            # read mask
            if maskbit:
                mask_key = self._buffered_read(4)

            # if frame payload is shorter than the requested data, read only the possible part
            readindex = chunk_endindex
            if payload_length < readindex:
                readindex = payload_length

            if readindex > 0:
                # get payload chunk
                payload = self._buffered_read(readindex)

                # unmask only the needed part
                if maskbit:
                    for index in range(chunk_startindex, readindex):
                        payload[index] ^= mask_key[index % 4]

                result = payload[chunk_startindex:readindex]
                self._payload_head = readindex
            else:
                payload = bytearray()

            # check if full frame arrived and reset readbuffer and payloadhead if needed
            if readindex == payload_length:
                self._readbuffer = bytearray()
                self._payload_head = 0

                # respond to non-binary opcodes, their arrival is not
                # guaranteed beacause of non-blocking sockets
                if opcode == WebsocketWrapper.OPCODE_CONNCLOSE:
                    frame = self._create_frame(
                        WebsocketWrapper.OPCODE_CONNCLOSE, payload, 0
                    )
                    self._socket.send(frame)

                if opcode == WebsocketWrapper.OPCODE_PING:
                    frame = self._create_frame(WebsocketWrapper.OPCODE_PONG, payload, 0)
                    self._socket.send(frame)

            # This isn't *proper* handling of continuation frames, but given
            # that we only support binary frames, it is *probably* good enough.
            if (
                opcode
                in (
                    WebsocketWrapper.OPCODE_BINARY,
                    WebsocketWrapper.OPCODE_CONTINUATION,
                )
                and payload_length > 0
            ):
                return result
            raise BlockingIOError

        except ConnectionError:
            self.connected = False
            return b""

    def _send_impl(self, data):
        """
        Send
        """

        # if previous frame was sent successfully
        if len(self._sendbuffer) == 0:
            # create websocket frame
            frame = self._create_frame(WebsocketWrapper.OPCODE_BINARY, bytearray(data))
            self._sendbuffer.extend(frame)
            self._requested_size = len(data)

        # try to write out as much as possible
        length = self._socket.send(self._sendbuffer)

        self._sendbuffer = self._sendbuffer[length:]

        if len(self._sendbuffer) == 0:
            # buffer sent out completely, return with payload's size
            return self._requested_size
        # couldn't send whole data, request the same data again with 0 as sent length
        return 0

    def recv(self, length):
        """
        Return specific number of bytes.
        """

        return self._recv_impl(length)

    def read(self, length):
        """
        Read data.
        """

        return self._recv_impl(length)

    def send(self, data):
        """
        Send data.
        """

        return self._send_impl(data)

    def write(self, data):
        """
        Write data.
        """

        return self._send_impl(data)

    def close(self):
        """
        Close socket.
        """

        self._socket.close()

    def fileno(self):
        """
        Get fileno.
        """

        return self._socket.fileno()

    def pending(self):
        """
        Get pending flag.

        Fix for bug #131: a SSL socket may still have data available
        for reading without select() being aware of it.
        """

        if self._ssl:
            return self._socket.pending()
        # normal socket rely only on select()
        return 0

    def setblocking(self, flag):
        """
        Set blocking flag.
        """

        self._socket.setblocking(flag)
