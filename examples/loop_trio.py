#!/usr/bin/env python3

import socket
import uuid

import trio

import paho.mqtt.client as mqtt

client_id = 'paho-mqtt-python/issue72/' + str(uuid.uuid4())
topic = client_id
print("Using client_id / topic: " + client_id)


class TrioAsyncHelper:
    def __init__(self, client):
        self.client = client
        self.sock = None
        self._event_large_write = trio.Event()

        self.client.on_socket_open = self.on_socket_open
        self.client.on_socket_register_write = self.on_socket_register_write
        self.client.on_socket_unregister_write = self.on_socket_unregister_write

    async def read_loop(self):
        while True:
            await trio.hazmat.wait_readable(self.sock)
            self.client.loop_read()

    async def write_loop(self):
        while True:
            await self._event_large_write.wait()
            await trio.hazmat.wait_writable(self.sock)
            self.client.loop_write()

    async def misc_loop(self):
        print("misc_loop started")
        while self.client.loop_misc() == mqtt.MQTT_ERR_SUCCESS:
            await trio.sleep(1)
        print("misc_loop finished")

    def on_socket_open(self, client, userdata, sock):
        print("Socket opened")
        self.sock = sock
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2048)

    def on_socket_register_write(self, client, userdata, sock):
        print('large write request')
        self._event_large_write.set()

    def on_socket_unregister_write(self, client, userdata, sock):
        print("finished large write")
        self._event_large_write = trio.Event()


class TrioAsyncMqttExample:
    def on_connect(self, client, userdata, flags, rc):
        print("Subscribing")
        client.subscribe(topic)

    def on_message(self, client, userdata, msg):
        print("Got response with {} bytes".format(len(msg.payload)))

    def on_disconnect(self, client, userdata, rc):
        print('Disconnect result {}'.format(rc))

    async def test_write(self, cancel_scope: trio.CancelScope):
        for c in range(3):
            await trio.sleep(5)
            print("Publishing")
            self.client.publish(topic, b'Hello' * 40000, qos=1)
        cancel_scope.cancel()

    async def main(self):
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        trio_helper = TrioAsyncHelper(self.client)

        self.client.connect('mqtt.eclipseprojects.io', 1883, 60)

        async with trio.open_nursery() as nursery:
            nursery.start_soon(trio_helper.read_loop)
            nursery.start_soon(trio_helper.write_loop)
            nursery.start_soon(trio_helper.misc_loop)
            nursery.start_soon(self.test_write, nursery.cancel_scope)

        self.client.disconnect()
        print("Disconnected")


print("Starting")
trio.run(TrioAsyncMqttExample().main)
print("Finished")
