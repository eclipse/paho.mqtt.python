"""
*******************************************************************
  Copyright (c) 2013, 2019 IBM Corp.

  All rights reserved. This program and the accompanying materials
  are made available under the terms of the Eclipse Public License v1.0
  and Eclipse Distribution License v1.0 which accompany this distribution.

  The Eclipse Public License is available at
     http://www.eclipse.org/legal/epl-v10.html
  and the Eclipse Distribution License is available at
    http://www.eclipse.org/org/documents/edl-v10.php.

  Contributors:
     Ian Craggs - initial implementation and/or documentation
*******************************************************************
"""

import unittest
import time
import threading
import getopt
import sys
import logging
import traceback

import paho.mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCodes
from paho.mqtt.subscribeoptions import SubscribeOptions
from paho.mqtt.packettypes import PacketTypes
import paho.mqtt.client


class Callbacks:

    def __init__(self):
        self.messages = []
        self.publisheds = []
        self.subscribeds = []
        self.unsubscribeds = []
        self.disconnecteds = []
        self.connecteds = []

    def __str__(self):
        return str(self.messages) + str(self.messagedicts) + str(self.publisheds) + \
            str(self.subscribeds) + \
            str(self.unsubscribeds) + str(self.disconnects)

    def clear(self):
        self.__init__()

    def on_connect(self, client, userdata, flags, reasonCode, properties):
        self.connecteds.append({"userdata": userdata, "flags": flags,
                                "reasonCode": reasonCode, "properties": properties})

    def wait(self, alist, timeout=2):
        interval = 0.2
        total = 0
        while len(alist) == 0 and total < timeout:
            time.sleep(interval)
            total += interval
        return alist.pop(0)  # if len(alist) > 0 else None

    def wait_connected(self):
        return self.wait(self.connecteds)

    def on_disconnect(self, client, userdata, reasonCode, properties=None):
        self.disconnecteds.append(
            {"reasonCode": reasonCode, "properties": properties})

    def wait_disconnected(self):
        return self.wait(self.disconnecteds)

    def on_message(self, client, userdata, message):
        self.messages.append({"userdata": userdata, "message": message})

    def published(self, client, userdata, msgid):
        self.publisheds.append(msgid)

    def wait_published(self):
        return self.wait(self.publisheds)

    def on_subscribe(self, client, userdata, mid, reasonCodes, properties):
        self.subscribeds.append({"mid": mid, "userdata": userdata,
                                 "properties": properties, "reasonCodes": reasonCodes})

    def wait_subscribed(self):
        return self.wait(self.subscribeds)

    def unsubscribed(self, client, userdata, mid, properties, reasonCodes):
        self.unsubscribeds.append({"mid": mid, "userdata": userdata,
                                   "properties": properties, "reasonCodes": reasonCodes})

    def wait_unsubscribed(self):
        return self.wait(self.unsubscribeds)

    def on_log(self, client, userdata, level, buf):
        print(buf)

    def register(self, client):
        client.on_connect = self.on_connect
        client.on_subscribe = self.on_subscribe
        client.on_publish = self.published
        client.on_unsubscribe = self.unsubscribed
        client.on_message = self.on_message
        client.on_disconnect = self.on_disconnect
        client.on_log = self.on_log


def cleanRetained(port):
    callback = Callbacks()
    curclient = paho.mqtt.client.Client("clean retained".encode("utf-8"),
                                        protocol=paho.mqtt.client.MQTTv5)
    curclient.loop_start()
    callback.register(curclient)
    curclient.connect(host="localhost", port=port)
    response = callback.wait_connected()
    curclient.subscribe("#", options=SubscribeOptions(qos=0))
    response = callback.wait_subscribed()  # wait for retained messages to arrive
    time.sleep(1)
    for message in callback.messages:
        logging.info("deleting retained message for topic", message["message"])
        curclient.publish(message["message"].topic, b"", 0, retain=True)
    curclient.disconnect()
    curclient.loop_stop()
    time.sleep(.1)


def cleanup(port):
    # clean all client state
    print("clean up starting")
    clientids = ("aclient", "bclient")

    for clientid in clientids:
        curclient = paho.mqtt.client.Client(clientid.encode(
            "utf-8"), protocol=paho.mqtt.client.MQTTv5)
        curclient.loop_start()
        curclient.connect(host="localhost", port=port, clean_start=True)
        time.sleep(.1)
        curclient.disconnect()
        time.sleep(.1)
        curclient.loop_stop()

    # clean retained messages
    cleanRetained(port)
    print("clean up finished")


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global callback, callback2, aclient, bclient

        sys.path.append("paho.mqtt.testing/interoperability/")
        try:
            import mqtt.brokers
        except ImportError:
            raise unittest.SkipTest("paho.mqtt.testing not present.")

        cls._test_broker = threading.Thread(
            target=mqtt.brokers.run,
            kwargs={
                "config": ["listener 0"],
            },
        )
        cls._test_broker.daemon = True
        cls._test_broker.start()
        # Wait a bit for TCP server to bind to an address
        time.sleep(0.5)
        # Hack to find the port used by the test broker...
        cls._test_broker_port = mqtt.brokers.listeners.TCPListeners.server.socket.getsockname()[1]
        setData()
        cleanup(cls._test_broker_port)

        callback = Callbacks()
        callback2 = Callbacks()

        #aclient = mqtt_client.Client(b"\xEF\xBB\xBF" + "myclientid".encode("utf-8"))
        #aclient = mqtt_client.Client("myclientid".encode("utf-8"))
        aclient = paho.mqtt.client.Client("aclient".encode(
            "utf-8"), protocol=paho.mqtt.client.MQTTv5)
        callback.register(aclient)

        bclient = paho.mqtt.client.Client("bclient".encode(
            "utf-8"), protocol=paho.mqtt.client.MQTTv5)
        callback2.register(bclient)

    @classmethod
    def tearDownClass(cls):
        # Another hack to stop the test broker... we rely on fact that it use a sockserver.TCPServer
        import mqtt.brokers
        mqtt.brokers.listeners.TCPListeners.server.shutdown()
        cls._test_broker.join(5)

    def waitfor(self, queue, depth, limit):
        total = 0
        while len(queue) < depth and total < limit:
            interval = .5
            total += interval
            time.sleep(interval)

    def test_basic(self):
        aclient.connect(host="localhost", port=self._test_broker_port)
        aclient.loop_start()
        response = callback.wait_connected()
        self.assertEqual(response["reasonCode"].getName(), "Success")

        aclient.subscribe(topics[0], options=SubscribeOptions(qos=2))
        response = callback.wait_subscribed()
        self.assertEqual(response["reasonCodes"][0].getName(), "Granted QoS 2")

        aclient.publish(topics[0], b"qos 0")
        aclient.publish(topics[0], b"qos 1", 1)
        aclient.publish(topics[0], b"qos 2", 2)
        i = 0
        while len(callback.messages) < 3 and i < 10:
            time.sleep(.2)
            i += 1
        self.assertEqual(len(callback.messages), 3)
        aclient.disconnect()

        callback.clear()
        aclient.loop_stop()

    def test_retained_message(self):
        qos0topic = "fromb/qos 0"
        qos1topic = "fromb/qos 1"
        qos2topic = "fromb/qos2"
        wildcardtopic = "fromb/+"

        publish_properties = Properties(PacketTypes.PUBLISH)
        publish_properties.UserProperty = ("a", "2")
        publish_properties.UserProperty = ("c", "3")

        # retained messages
        callback.clear()
        aclient.connect(host="localhost", port=self._test_broker_port)
        aclient.loop_start()
        response = callback.wait_connected()
        aclient.publish(topics[1], b"qos 0", 0,
                        retain=True, properties=publish_properties)
        aclient.publish(topics[2], b"qos 1", 1,
                        retain=True, properties=publish_properties)
        aclient.publish(topics[3], b"qos 2", 2,
                        retain=True, properties=publish_properties)
        # wait until those messages are published
        time.sleep(1)
        aclient.subscribe(wildtopics[5], options=SubscribeOptions(qos=2))
        response = callback.wait_subscribed()
        self.assertEqual(response["reasonCodes"][0].getName(), "Granted QoS 2")

        time.sleep(1)
        aclient.disconnect()
        aclient.loop_stop()

        self.assertEqual(len(callback.messages), 3)
        userprops = callback.messages[0]["message"].properties.UserProperty
        self.assertTrue(userprops in [[("a", "2"), ("c", "3")], [
                        ("c", "3"), ("a", "2")]], userprops)
        userprops = callback.messages[1]["message"].properties.UserProperty
        self.assertTrue(userprops in [[("a", "2"), ("c", "3")], [
                        ("c", "3"), ("a", "2")]], userprops)
        userprops = callback.messages[2]["message"].properties.UserProperty
        self.assertTrue(userprops in [[("a", "2"), ("c", "3")], [
                        ("c", "3"), ("a", "2")]], userprops)
        qoss = [callback.messages[i]["message"].qos for i in range(3)]
        self.assertTrue(1 in qoss and 2 in qoss and 0 in qoss, qoss)

        cleanRetained(self._test_broker_port)

    def test_will_message(self):
        # will messages and keep alive
        callback.clear()
        callback2.clear()
        self.assertEqual(len(callback2.messages), 0, callback2.messages)

        will_properties = Properties(PacketTypes.WILLMESSAGE)
        will_properties.WillDelayInterval = 0  # this is the default anyway
        will_properties.UserProperty = ("a", "2")
        will_properties.UserProperty = ("c", "3")

        aclient.will_set(topics[2], payload=b"will message",
                         properties=will_properties)

        aclient.connect(host="localhost", port=self._test_broker_port, keepalive=2)
        aclient.loop_start()
        response = callback.wait_connected()
        bclient.connect(host="localhost", port=self._test_broker_port)
        bclient.loop_start()
        response = callback2.wait_connected()
        bclient.subscribe(topics[2], qos=2)
        response = callback2.wait_subscribed()
        self.assertEqual(response["reasonCodes"][0].getName(), "Granted QoS 2")

        # keep alive timeout ought to be triggered so the will message is received
        aclient.loop_stop()  # so that pings aren't sent
        self.waitfor(callback2.messages, 1, 10)
        bclient.disconnect()
        bclient.loop_stop()
        # should have the will message
        self.assertEqual(len(callback2.messages), 1, callback2.messages)
        props = callback2.messages[0]["message"].properties
        self.assertEqual(props.UserProperty, [("a", "2"), ("c", "3")])

    def test_zero_length_clientid(self):
        logging.info("Zero length clientid test starting")

        callback0 = Callbacks()

        client0 = paho.mqtt.client.Client(protocol=paho.mqtt.client.MQTTv5)
        callback0.register(client0)
        client0.loop_start()
        # should not be rejected
        client0.connect(host="localhost", port=self._test_broker_port, clean_start=False)
        response = callback0.wait_connected()
        self.assertEqual(response["reasonCode"].getName(), "Success")
        self.assertTrue(
            len(response["properties"].AssignedClientIdentifier) > 0)
        client0.disconnect()
        client0.loop_stop()

        client0 = paho.mqtt.client.Client(protocol=paho.mqtt.client.MQTTv5)
        callback0.register(client0)
        client0.loop_start()
        client0.connect(host="localhost", port=self._test_broker_port)  # should work
        response = callback0.wait_connected()
        self.assertEqual(response["reasonCode"].getName(), "Success")
        self.assertTrue(
            len(response["properties"].AssignedClientIdentifier) > 0)
        client0.disconnect()
        client0.loop_stop()

        # when we supply a client id, we should not get one assigned
        client0 = paho.mqtt.client.Client(
            "client0", protocol=paho.mqtt.client.MQTTv5)
        callback0.register(client0)
        client0.loop_start()
        client0.connect(host="localhost", port=self._test_broker_port)  # should work
        response = callback0.wait_connected()
        self.assertEqual(response["reasonCode"].getName(), "Success")
        self.assertFalse(
            hasattr(response["properties"], "AssignedClientIdentifier"))
        client0.disconnect()
        client0.loop_stop()

    def test_offline_message_queueing(self):
        # message queueing for offline clients
        cleanRetained(self._test_broker_port)
        ocallback = Callbacks()
        clientid = "offline message queueing".encode("utf-8")

        oclient = paho.mqtt.client.Client(
            clientid, protocol=paho.mqtt.client.MQTTv5)
        ocallback.register(oclient)
        connect_properties = Properties(PacketTypes.CONNECT)
        connect_properties.SessionExpiryInterval = 99999
        oclient.loop_start()
        oclient.connect(host="localhost", port=self._test_broker_port, properties=connect_properties)
        response = ocallback.wait_connected()
        oclient.subscribe(wildtopics[5], qos=2)
        response = ocallback.wait_subscribed()
        oclient.disconnect()
        oclient.loop_stop()

        bclient.loop_start()
        bclient.connect(host="localhost", port=self._test_broker_port)
        response = callback2.wait_connected()
        bclient.publish(topics[1], b"qos 0", 0)
        bclient.publish(topics[2], b"qos 1", 1)
        bclient.publish(topics[3], b"qos 2", 2)
        time.sleep(2)
        bclient.disconnect()
        bclient.loop_stop()

        oclient = paho.mqtt.client.Client(
            clientid, protocol=paho.mqtt.client.MQTTv5)
        ocallback.register(oclient)
        oclient.loop_start()
        oclient.connect(host="localhost", port=self._test_broker_port, clean_start=False)
        response = ocallback.wait_connected()
        time.sleep(2)
        oclient.disconnect()
        oclient.loop_stop()

        self.assertTrue(len(ocallback.messages) in [
                        2, 3], len(ocallback.messages))
        logging.info("This server %s queueing QoS 0 messages for offline clients" %
                     ("is" if len(ocallback.messages) == 3 else "is not"))

    def test_overlapping_subscriptions(self):
        # overlapping subscriptions. When there is more than one matching subscription for the same client for a topic,
        # the server may send back one message with the highest QoS of any matching subscription, or one message for
        # each subscription with a matching QoS.
        ocallback = Callbacks()
        clientid = "overlapping subscriptions".encode("utf-8")

        oclient = paho.mqtt.client.Client(
            clientid, protocol=paho.mqtt.client.MQTTv5)
        ocallback.register(oclient)

        oclient.loop_start()
        oclient.connect(host="localhost", port=self._test_broker_port)
        ocallback.wait_connected()
        oclient.subscribe([(wildtopics[6], SubscribeOptions(qos=2)),
                           (wildtopics[0], SubscribeOptions(qos=1))])
        ocallback.wait_subscribed()
        oclient.publish(topics[3], b"overlapping topic filters", 2)
        ocallback.wait_published()
        time.sleep(1)
        self.assertTrue(len(ocallback.messages) in [1, 2], ocallback.messages)
        if len(ocallback.messages) == 1:
            logging.info(
                "This server is publishing one message for all matching overlapping subscriptions, not one for each.")
            self.assertEqual(
                ocallback.messages[0]["message"].qos, 2, ocallback.messages[0]["message"].qos)
        else:
            logging.info(
                "This server is publishing one message per each matching overlapping subscription.")
            self.assertTrue((ocallback.messages[0]["message"].qos == 2 and ocallback.messages[1]["message"].qos == 1) or
                            (ocallback.messages[0]["message"].qos == 1 and ocallback.messages[1]["message"].qos == 2), callback.messages)
        oclient.disconnect()
        oclient.loop_stop()
        ocallback.clear()

    def test_subscribe_failure(self):
        # Subscribe failure.  A new feature of MQTT 3.1.1 is the ability to send back negative reponses to subscribe
        # requests.  One way of doing this is to subscribe to a topic which is not allowed to be subscribed to.
        logging.info("Subscribe failure test starting")

        ocallback = Callbacks()
        clientid = "subscribe failure".encode("utf-8")
        oclient = paho.mqtt.client.Client(
            clientid, protocol=paho.mqtt.client.MQTTv5)
        ocallback.register(oclient)
        oclient.loop_start()
        oclient.connect(host="localhost", port=self._test_broker_port)
        ocallback.wait_connected()
        oclient.subscribe(nosubscribe_topics[0], qos=2)
        response = ocallback.wait_subscribed()

        self.assertEqual(response["reasonCodes"][0].getName(), "Unspecified error",
                         "return code should be 0x80 %s" % response["reasonCodes"][0].getName())
        oclient.disconnect()
        oclient.loop_stop()

    def test_unsubscribe(self):
        callback2.clear()
        bclient.connect(host="localhost", port=self._test_broker_port)
        bclient.loop_start()
        callback2.wait_connected()
        bclient.subscribe(topics[0], qos=2)
        callback2.wait_subscribed()
        bclient.subscribe(topics[1], qos=2)
        callback2.wait_subscribed()
        bclient.subscribe(topics[2], qos=2)
        callback2.wait_subscribed()
        time.sleep(1)  # wait for any retained messages, hopefully
        # Unsubscribe from one topic
        bclient.unsubscribe(topics[0])
        callback2.wait_unsubscribed()
        callback2.clear()  # if there were any retained messsages

        aclient.connect(host="localhost", port=self._test_broker_port)
        aclient.loop_start()
        callback.wait_connected()
        aclient.publish(topics[0], b"topic 0 - unsubscribed", 1, retain=False)
        aclient.publish(topics[1], b"topic 1", 1, retain=False)
        aclient.publish(topics[2], b"topic 2", 1, retain=False)
        time.sleep(2)

        bclient.disconnect()
        bclient.loop_stop()
        aclient.disconnect()
        aclient.loop_stop()
        self.assertEqual(len(callback2.messages), 2, callback2.messages)

    def new_client(self, clientid):
        callback = Callbacks()
        client = paho.mqtt.client.Client(clientid.encode(
            "utf-8"), protocol=paho.mqtt.client.MQTTv5)
        callback.register(client)
        client.loop_start()
        return client, callback

    def test_session_expiry(self):
        # no session expiry property == never expire

        connect_properties = Properties(PacketTypes.CONNECT)
        connect_properties.SessionExpiryInterval = 0  # expire immediately

        clientid = "session expiry"

        eclient, ecallback = self.new_client(clientid)

        eclient.connect(host="localhost", port=self._test_broker_port, properties=connect_properties)
        connack = ecallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], False)
        eclient.subscribe(topics[0], qos=2)
        ecallback.wait_subscribed()
        eclient.disconnect()
        ecallback.wait_disconnected()
        eclient.loop_stop()

        fclient, fcallback = self.new_client(clientid)

        # session should immediately expire
        fclient.connect_async(host="localhost", port=self._test_broker_port, clean_start=False,
                              properties=connect_properties)
        connack = fcallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], False)
        fclient.disconnect()
        fcallback.wait_disconnected()

        connect_properties.SessionExpiryInterval = 5

        eclient, ecallback = self.new_client(clientid)

        eclient.connect(host="localhost", port=self._test_broker_port, properties=connect_properties)
        connack = ecallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], False)
        eclient.subscribe(topics[0], qos=2)
        ecallback.wait_subscribed()
        eclient.disconnect()
        ecallback.wait_disconnected()
        eclient.loop_stop()

        time.sleep(2)
        # session should still exist
        fclient, fcallback = self.new_client(clientid)
        fclient.connect(host="localhost", port=self._test_broker_port, clean_start=False,
                        properties=connect_properties)
        connack = fcallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], True)
        fclient.disconnect()
        fcallback.wait_disconnected()
        fclient.loop_stop()

        time.sleep(6)
        # session should not exist
        fclient, fcallback = self.new_client(clientid)
        fclient.connect(host="localhost", port=self._test_broker_port, clean_start=False,
                        properties=connect_properties)
        connack = fcallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], False)
        fclient.disconnect()
        fcallback.wait_disconnected()
        fclient.loop_stop()

        eclient, ecallback = self.new_client(clientid)
        connect_properties.SessionExpiryInterval = 1
        connack = eclient.connect(
            host="localhost", port=self._test_broker_port, properties=connect_properties)
        connack = ecallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], False)
        eclient.subscribe(topics[0], qos=2)
        ecallback.wait_subscribed()
        disconnect_properties = Properties(PacketTypes.DISCONNECT)
        disconnect_properties.SessionExpiryInterval = 5
        eclient.disconnect(properties=disconnect_properties)
        ecallback.wait_disconnected()
        eclient.loop_stop()

        time.sleep(3)
        # session should still exist as we changed the expiry interval on disconnect
        fclient, fcallback = self.new_client(clientid)
        fclient.connect(host="localhost", port=self._test_broker_port, clean_start=False,
                        properties=connect_properties)
        connack = fcallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], True)
        disconnect_properties.SessionExpiryInterval = 0
        fclient.disconnect(properties=disconnect_properties)
        fcallback.wait_disconnected()
        fclient.loop_stop()

        # session should immediately expire
        fclient, fcallback = self.new_client(clientid)
        fclient.connect(host="localhost", port=self._test_broker_port, clean_start=False,
                        properties=connect_properties)
        connack = fcallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], False)
        fclient.disconnect()
        fcallback.wait_disconnected()
        fclient.loop_stop()

        fclient.loop_stop()
        eclient.loop_stop()

    def test_user_properties(self):
        clientid = "user properties"
        uclient, ucallback = self.new_client(clientid)
        uclient.loop_start()
        uclient.connect(host="localhost", port=self._test_broker_port)
        ucallback.wait_connected()

        uclient.subscribe(topics[0], qos=2)
        ucallback.wait_subscribed()

        publish_properties = Properties(PacketTypes.PUBLISH)
        publish_properties.UserProperty = ("a", "2")
        publish_properties.UserProperty = ("c", "3")
        uclient.publish(topics[0], b"", 0, retain=False,
                        properties=publish_properties)
        uclient.publish(topics[0], b"", 1, retain=False,
                        properties=publish_properties)
        uclient.publish(topics[0], b"", 2, retain=False,
                        properties=publish_properties)
        count = 0
        while len(ucallback.messages) < 3 and count < 50:
            time.sleep(.1)
            count += 1
        uclient.disconnect()
        ucallback.wait_disconnected()
        uclient.loop_stop()
        self.assertEqual(len(ucallback.messages), 3, ucallback.messages)
        userprops = ucallback.messages[0]["message"].properties.UserProperty
        self.assertTrue(userprops in [[("a", "2"), ("c", "3")], [
                        ("c", "3"), ("a", "2")]], userprops)
        userprops = ucallback.messages[1]["message"].properties.UserProperty
        self.assertTrue(userprops in [[("a", "2"), ("c", "3")], [
                        ("c", "3"), ("a", "2")]], userprops)
        userprops = ucallback.messages[2]["message"].properties.UserProperty
        self.assertTrue(userprops in [[("a", "2"), ("c", "3")], [
                        ("c", "3"), ("a", "2")]], userprops)
        qoss = [ucallback.messages[i]["message"].qos for i in range(3)]
        self.assertTrue(1 in qoss and 2 in qoss and 0 in qoss, qoss)

    def test_payload_format(self):
        clientid = "payload format"
        pclient, pcallback = self.new_client(clientid)
        pclient.loop_start()
        pclient.connect_async(host="localhost", port=self._test_broker_port)
        response = pcallback.wait_connected()

        pclient.subscribe(topics[0], qos=2)
        response = pcallback.wait_subscribed()
        publish_properties = Properties(PacketTypes.PUBLISH)
        publish_properties.PayloadFormatIndicator = 1
        publish_properties.ContentType = "My name"
        info = pclient.publish(
            topics[0], b"qos 0", 0, retain=False, properties=publish_properties)
        info.wait_for_publish()
        info = pclient.publish(
            topics[0], b"qos 1", 1, retain=False, properties=publish_properties)
        info.wait_for_publish()
        info = pclient.publish(
            topics[0], b"qos 2", 2, retain=False, properties=publish_properties)
        info.wait_for_publish()

        count = 0
        while len(pcallback.messages) < 3 and count < 50:
            time.sleep(.1)
            count += 1
        pclient.disconnect()
        pcallback.wait_disconnected()
        pclient.loop_stop()

        self.assertEqual(len(pcallback.messages), 3, pcallback.messages)
        props = pcallback.messages[0]["message"].properties
        self.assertEqual(props.ContentType, "My name", props.ContentType)
        self.assertEqual(props.PayloadFormatIndicator,
                         1, props.PayloadFormatIndicator)
        props = pcallback.messages[1]["message"].properties
        self.assertEqual(props.ContentType, "My name", props.ContentType)
        self.assertEqual(props.PayloadFormatIndicator,
                         1, props.PayloadFormatIndicator)
        props = pcallback.messages[2]["message"].properties
        self.assertEqual(props.ContentType, "My name", props.ContentType)
        self.assertEqual(props.PayloadFormatIndicator,
                         1, props.PayloadFormatIndicator)
        qoss = [pcallback.messages[i]["message"].qos for i in range(3)]
        self.assertTrue(1 in qoss and 2 in qoss and 0 in qoss, qoss)

    def test_message_expiry(self):
        clientid = "message expiry"

        connect_properties = Properties(PacketTypes.CONNECT)
        connect_properties.SessionExpiryInterval = 99999

        lbclient, lbcallback = self.new_client(clientid+" b")
        lbclient.loop_start()
        lbclient.connect(host="localhost", port=self._test_broker_port, properties=connect_properties)
        response = lbcallback.wait_connected()
        lbclient.subscribe(topics[0], qos=2)
        response = lbcallback.wait_subscribed()
        disconnect_properties = Properties(PacketTypes.DISCONNECT)
        disconnect_properties.SessionExpiryInterval = 999999999
        lbclient.disconnect(properties=disconnect_properties)
        lbcallback.wait_disconnected()
        lbclient.loop_stop()

        laclient, lacallback = self.new_client(clientid+" a")
        laclient.loop_start()
        laclient.connect(host="localhost", port=self._test_broker_port)
        publish_properties = Properties(PacketTypes.PUBLISH)
        publish_properties.MessageExpiryInterval = 1
        laclient.publish(topics[0], b"qos 1 - expire", 1,
                         retain=False, properties=publish_properties)
        laclient.publish(topics[0], b"qos 2 - expire", 2,
                         retain=False, properties=publish_properties)

        publish_properties = Properties(PacketTypes.PUBLISH)
        publish_properties.MessageExpiryInterval = 6
        laclient.publish(topics[0], b"qos 1 - don't expire",
                         1, retain=False, properties=publish_properties)
        laclient.publish(topics[0], b"qos 2 - don't expire",
                         2, retain=False, properties=publish_properties)

        time.sleep(3)
        lbclient, lbcallback = self.new_client(clientid+" b")
        lbclient.loop_start()
        lbclient.connect(host="localhost", port=self._test_broker_port, clean_start=False)
        lbcallback.wait_connected()
        self.waitfor(lbcallback.messages, 1, 3)
        time.sleep(1)
        self.assertEqual(len(lbcallback.messages), 2, lbcallback.messages)
        self.assertTrue(lbcallback.messages[0]["message"].properties.MessageExpiryInterval < 6,
                        lbcallback.messages[0]["message"].properties.MessageExpiryInterval)
        self.assertTrue(lbcallback.messages[1]["message"].properties.MessageExpiryInterval < 6,
                        lbcallback.messages[1]["message"].properties.MessageExpiryInterval)
        laclient.disconnect()
        lacallback.wait_disconnected()
        laclient.loop_stop()

        lbclient.disconnect()
        lbcallback.wait_disconnected()
        lbclient.loop_stop()

    def test_subscribe_options(self):
        # noLocal
        clientid = 'subscribe options - noLocal'

        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port)
        lacallback.wait_connected()
        laclient.loop_start()
        laclient.subscribe(
            topics[0], options=SubscribeOptions(qos=2, noLocal=True))
        lacallback.wait_subscribed()

        lbclient, lbcallback = self.new_client(clientid+" b")
        lbclient.connect(host="localhost", port=self._test_broker_port)
        lbcallback.wait_connected()
        lbclient.loop_start()
        lbclient.subscribe(
            topics[0], options=SubscribeOptions(qos=2, noLocal=True))
        lbcallback.wait_subscribed()

        laclient.publish(topics[0], b"noLocal test", 1, retain=False)
        self.waitfor(lbcallback.messages, 1, 3)
        time.sleep(1)

        self.assertEqual(lacallback.messages, [], lacallback.messages)
        self.assertEqual(len(lbcallback.messages), 1, lbcallback.messages)
        laclient.disconnect()
        lacallback.wait_disconnected()
        lbclient.disconnect()
        lbcallback.wait_disconnected()
        laclient.loop_stop()
        lbclient.loop_stop()

        # retainAsPublished
        clientid = 'subscribe options - retain as published'
        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port)
        lacallback.wait_connected()
        laclient.subscribe(topics[0], options=SubscribeOptions(
            qos=2, retainAsPublished=True))
        lacallback.wait_subscribed()
        self.waitfor(lacallback.subscribeds, 1, 3)
        laclient.publish(
            topics[0], b"retain as published false", 1, retain=False)
        laclient.publish(
            topics[0], b"retain as published true", 1, retain=True)

        self.waitfor(lacallback.messages, 2, 3)
        time.sleep(1)

        self.assertEqual(len(lacallback.messages), 2, lacallback.messages)
        laclient.disconnect()
        lacallback.wait_disconnected()
        laclient.loop_stop()
        self.assertEqual(lacallback.messages[0]["message"].retain, False)
        self.assertEqual(lacallback.messages[1]["message"].retain, True)

        # retainHandling
        clientid = 'subscribe options - retain handling'
        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port)
        lacallback.wait_connected()
        laclient.publish(topics[1], b"qos 0", 0, retain=True)
        laclient.publish(topics[2], b"qos 1", 1, retain=True)
        laclient.publish(topics[3], b"qos 2", 2, retain=True)
        time.sleep(1)

        # retain handling 1 only gives us retained messages on a new subscription
        laclient.subscribe(
            wildtopics[5], options=SubscribeOptions(2, retainHandling=1))
        lacallback.wait_subscribed()
        self.assertEqual(len(lacallback.messages), 3)
        qoss = [lacallback.messages[i]["message"].qos for i in range(3)]
        self.assertTrue(1 in qoss and 2 in qoss and 0 in qoss, qoss)
        lacallback.clear()
        laclient.subscribe(
            wildtopics[5], options=SubscribeOptions(2, retainHandling=1))
        lacallback.wait_subscribed()
        time.sleep(1)
        self.assertEqual(len(lacallback.messages), 0)

        # remove that subscription
        properties = Properties(PacketTypes.UNSUBSCRIBE)
        properties.UserProperty = ("a", "2")
        properties.UserProperty = ("c", "3")
        laclient.unsubscribe(wildtopics[5], properties)
        response = lacallback.wait_unsubscribed()

        # check that we really did remove that subscription
        laclient.subscribe(
            wildtopics[5], options=SubscribeOptions(2, retainHandling=1))
        lacallback.wait_subscribed()
        self.assertEqual(len(lacallback.messages), 3)
        qoss = [lacallback.messages[i]["message"].qos for i in range(3)]
        self.assertTrue(1 in qoss and 2 in qoss and 0 in qoss, qoss)
        lacallback.clear()
        laclient.subscribe(
            wildtopics[5], options=SubscribeOptions(2, retainHandling=1))
        lacallback.wait_subscribed()
        time.sleep(1)
        self.assertEqual(len(lacallback.messages), 0)

        # remove that subscription
        properties = Properties(PacketTypes.UNSUBSCRIBE)
        properties.UserProperty = ("a", "2")
        properties.UserProperty = ("c", "3")
        laclient.unsubscribe(wildtopics[5], properties)
        response = lacallback.wait_unsubscribed()

        lacallback.clear()
        laclient.subscribe(
            wildtopics[5], options=SubscribeOptions(2, retainHandling=2))
        lacallback.wait_subscribed()
        self.assertEqual(len(lacallback.messages), 0)
        laclient.subscribe(
            wildtopics[5], options=SubscribeOptions(2, retainHandling=2))
        lacallback.wait_subscribed()
        self.assertEqual(len(lacallback.messages), 0)

        # remove that subscription
        laclient.unsubscribe(wildtopics[5])
        response = lacallback.wait_unsubscribed()

        laclient.subscribe(
            wildtopics[5], options=SubscribeOptions(2, retainHandling=0))
        lacallback.wait_subscribed()
        self.assertEqual(len(lacallback.messages), 3)
        qoss = [lacallback.messages[i]["message"].qos for i in range(3)]
        self.assertTrue(1 in qoss and 2 in qoss and 0 in qoss, qoss)
        lacallback.clear()
        laclient.subscribe(
            wildtopics[5], options=SubscribeOptions(2, retainHandling=0))
        time.sleep(1)
        self.assertEqual(len(lacallback.messages), 3)
        qoss = [lacallback.messages[i]["message"].qos for i in range(3)]
        self.assertTrue(1 in qoss and 2 in qoss and 0 in qoss, qoss)
        laclient.disconnect()
        lacallback.wait_disconnected()
        laclient.loop_stop()

        cleanRetained(self._test_broker_port)

    def test_subscription_identifiers(self):
        clientid = 'subscription identifiers'

        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port)
        lacallback.wait_connected()
        laclient.loop_start()

        sub_properties = Properties(PacketTypes.SUBSCRIBE)
        sub_properties.SubscriptionIdentifier = 456789
        laclient.subscribe(topics[0], qos=2, properties=sub_properties)
        lacallback.wait_subscribed()

        lbclient, lbcallback = self.new_client(clientid+" b")
        lbclient.connect(host="localhost", port=self._test_broker_port)
        lbcallback.wait_connected()
        lbclient.loop_start()
        sub_properties = Properties(PacketTypes.SUBSCRIBE)
        sub_properties.SubscriptionIdentifier = 2
        lbclient.subscribe(topics[0], qos=2, properties=sub_properties)
        lbcallback.wait_subscribed()

        sub_properties.clear()
        sub_properties.SubscriptionIdentifier = 3
        lbclient.subscribe(topics[0]+"/#", qos=2, properties=sub_properties)

        lbclient.publish(topics[0], b"sub identifier test", 1, retain=False)

        self.waitfor(lacallback.messages, 1, 3)
        self.assertEqual(len(lacallback.messages), 1, lacallback.messages)
        self.assertEqual(lacallback.messages[0]["message"].properties.SubscriptionIdentifier[0],
                         456789, lacallback.messages[0]["message"].properties.SubscriptionIdentifier)
        laclient.disconnect()
        lacallback.wait_disconnected()
        laclient.loop_stop()

        self.waitfor(lbcallback.messages, 1, 3)
        self.assertEqual(len(lbcallback.messages), 1, lbcallback.messages)
        expected_subsids = set([2, 3])
        received_subsids = set(
            lbcallback.messages[0]["message"].properties.SubscriptionIdentifier)
        self.assertEqual(received_subsids, expected_subsids, received_subsids)
        lbclient.disconnect()
        lbcallback.wait_disconnected()
        lbclient.loop_stop()

    def test_request_response(self):
        clientid = 'request response'

        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port)
        lacallback.wait_connected()
        laclient.loop_start()

        lbclient, lbcallback = self.new_client(clientid+" b")
        lbclient.connect(host="localhost", port=self._test_broker_port)
        lbcallback.wait_connected()
        lbclient.loop_start()

        laclient.subscribe(
            topics[0], options=SubscribeOptions(2, noLocal=True))
        lacallback.wait_subscribed()

        lbclient.subscribe(
            topics[0], options=SubscribeOptions(2, noLocal=True))
        lbcallback.wait_subscribed()

        publish_properties = Properties(PacketTypes.PUBLISH)
        publish_properties.ResponseTopic = topics[0]
        publish_properties.CorrelationData = b"334"
        # client a is the requester
        laclient.publish(topics[0], b"request", 1,
                         properties=publish_properties)

        # client b is the responder
        self.waitfor(lbcallback.messages, 1, 3)
        self.assertEqual(len(lbcallback.messages), 1, lbcallback.messages)
        self.assertEqual(lbcallback.messages[0]["message"].properties.ResponseTopic, topics[0],
                         lbcallback.messages[0]["message"].properties)
        self.assertEqual(lbcallback.messages[0]["message"].properties.CorrelationData, b"334",
                         lbcallback.messages[0]["message"].properties)

        lbclient.publish(lbcallback.messages[0]["message"].properties.ResponseTopic, b"response", 1,
                         properties=lbcallback.messages[0]["message"].properties)

        # client a gets the response
        self.waitfor(lacallback.messages, 1, 3)
        self.assertEqual(len(lacallback.messages), 1, lacallback.messages)

        laclient.disconnect()
        lacallback.wait_disconnected()
        laclient.loop_stop()
        lbclient.disconnect()
        lbcallback.wait_disconnected()
        lbclient.loop_stop()

    def test_client_topic_alias(self):
        clientid = 'client topic alias'

        # no server side topic aliases allowed
        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port)
        connack = lacallback.wait_connected()
        laclient.loop_start()

        publish_properties = Properties(PacketTypes.PUBLISH)
        publish_properties.TopicAlias = 0  # topic alias 0 not allowed
        laclient.publish(topics[0], "topic alias 0", 1,
                         properties=publish_properties)

        # should get back a disconnect with Topic alias invalid
        lacallback.wait_disconnected()
        laclient.loop_stop()

        connect_properties = Properties(PacketTypes.CONNECT)
        connect_properties.TopicAliasMaximum = 0  # server topic aliases not allowed
        connect_properties.SessionExpiryInterval = 99999
        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port, properties=connect_properties)
        connack = lacallback.wait_connected()
        clientTopicAliasMaximum = 0
        if hasattr(connack["properties"], "TopicAliasMaximum"):
            clientTopicAliasMaximum = connack["properties"].TopicAliasMaximum

        if clientTopicAliasMaximum == 0:
            laclient.disconnect()
            lacallback.wait_disconnected()
            laclient.loop_stop()
            return

        laclient.subscribe(topics[0], qos=2)
        lacallback.wait_subscribed()

        publish_properties = Properties(PacketTypes.PUBLISH)
        publish_properties.TopicAlias = 1
        laclient.publish(topics[0], b"topic alias 1",
                         1, properties=publish_properties)
        self.waitfor(lacallback.messages, 1, 3)
        self.assertEqual(len(lacallback.messages), 1, lacallback.messages)

        laclient.publish("", b"topic alias 2", 1,
                         properties=publish_properties)
        self.waitfor(lacallback.messages, 2, 3)
        self.assertEqual(len(lacallback.messages), 2, lacallback.messages)

        laclient.disconnect()  # should get rid of the topic aliases but not subscriptions
        lacallback.wait_disconnected()
        laclient.loop_stop()

        # check aliases have been deleted
        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port, clean_start=False,
                         properties=connect_properties)

        laclient.publish(topics[0], b"topic alias 3", 1)
        self.waitfor(lacallback.messages, 1, 3)
        self.assertEqual(len(lacallback.messages), 1, lacallback.messages)

        publish_properties = Properties(PacketTypes.PUBLISH)
        publish_properties.TopicAlias = 1
        laclient.publish("", b"topic alias 4", 1,
                         properties=publish_properties)

        # should get back a disconnect with Topic alias invalid
        lacallback.wait_disconnected()
        laclient.loop_stop()

    def test_server_topic_alias(self):
        clientid = 'server topic alias'

        serverTopicAliasMaximum = 1  # server topic alias allowed
        connect_properties = Properties(PacketTypes.CONNECT)
        connect_properties.TopicAliasMaximum = serverTopicAliasMaximum

        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port, properties=connect_properties)
        connack = lacallback.wait_connected()
        laclient.loop_start()
        clientTopicAliasMaximum = 0
        if hasattr(connack["properties"], "TopicAliasMaximum"):
            clientTopicAliasMaximum = connack["properties"].TopicAliasMaximum

        laclient.subscribe(topics[0], qos=2)
        lacallback.wait_subscribed()

        for qos in range(3):
            laclient.publish(topics[0], b"topic alias 1", qos)
        self.waitfor(lacallback.messages, 3, 3)
        self.assertEqual(len(lacallback.messages), 3, lacallback.messages)
        laclient.disconnect()
        lacallback.wait_disconnected()
        laclient.loop_stop()

        # first message should set the topic alias
        self.assertTrue(hasattr(
            lacallback.messages[0]["message"].properties, "TopicAlias"), lacallback.messages[0]["message"].properties)
        topicalias = lacallback.messages[0]["message"].properties.TopicAlias

        self.assertTrue(topicalias > 0)
        self.assertEqual(lacallback.messages[0]["message"].topic, topics[0])

        self.assertEqual(
            lacallback.messages[1]["message"].properties.TopicAlias, topicalias)
        self.assertEqual(lacallback.messages[1]["message"].topic, "")

        self.assertEqual(
            lacallback.messages[2]["message"].properties.TopicAlias, topicalias)
        self.assertEqual(lacallback.messages[2]["message"].topic, "")

        serverTopicAliasMaximum = 0  # no server topic alias allowed
        connect_properties = Properties(PacketTypes.CONNECT)
        # connect_properties.TopicAliasMaximum = serverTopicAliasMaximum # default is 0

        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port, properties=connect_properties)
        connack = lacallback.wait_connected()
        laclient.loop_start()

        clientTopicAliasMaximum = 0
        if hasattr(connack["properties"], "TopicAliasMaximum"):
            clientTopicAliasMaximum = connack["properties"].TopicAliasMaximum

        laclient.subscribe(topics[0], qos=2)
        lacallback.wait_subscribed()

        for qos in range(3):
            laclient.publish(topics[0], b"topic alias 2", qos)
        self.waitfor(lacallback.messages, 3, 3)
        self.assertEqual(len(lacallback.messages), 3, lacallback.messages)
        laclient.disconnect()
        lacallback.wait_disconnected()
        laclient.loop_stop()

        # No topic aliases
        self.assertFalse(hasattr(
            lacallback.messages[0]["message"].properties, "TopicAlias"), lacallback.messages[0]["message"].properties)
        self.assertFalse(hasattr(
            lacallback.messages[1]["message"].properties, "TopicAlias"), lacallback.messages[1]["message"].properties)
        self.assertFalse(hasattr(
            lacallback.messages[2]["message"].properties, "TopicAlias"), lacallback.messages[2]["message"].properties)

        serverTopicAliasMaximum = 0  # no server topic alias allowed
        connect_properties = Properties(PacketTypes.CONNECT)
        connect_properties.TopicAliasMaximum = serverTopicAliasMaximum  # default is 0

        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port, properties=connect_properties)
        connack = lacallback.wait_connected()
        laclient.loop_start()

        clientTopicAliasMaximum = 0
        if hasattr(connack["properties"], "TopicAliasMaximum"):
            clientTopicAliasMaximum = connack["properties"].TopicAliasMaximum

        laclient.subscribe(topics[0], qos=2)
        lacallback.wait_subscribed()

        for qos in range(3):
            laclient.publish(topics[0], b"topic alias 3", qos)
        self.waitfor(lacallback.messages, 3, 3)
        self.assertEqual(len(lacallback.messages), 3, lacallback.messages)
        laclient.disconnect()
        lacallback.wait_disconnected()
        laclient.loop_stop()

        # No topic aliases
        self.assertFalse(hasattr(
            lacallback.messages[0]["message"].properties, "TopicAlias"), lacallback.messages[0]["message"].properties)
        self.assertFalse(hasattr(
            lacallback.messages[1]["message"].properties, "TopicAlias"), lacallback.messages[1]["message"].properties)
        self.assertFalse(hasattr(
            lacallback.messages[2]["message"].properties, "TopicAlias"), lacallback.messages[2]["message"].properties)

    def test_maximum_packet_size(self):
        clientid = 'maximum packet size'

        # 1. server max packet size
        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port)
        connack = lacallback.wait_connected()
        laclient.loop_start()

        serverMaximumPacketSize = 2**28-1
        if hasattr(connack["properties"], "MaximumPacketSize"):
            serverMaximumPacketSize = connack["properties"].MaximumPacketSize

        if serverMaximumPacketSize < 65535:
            # publish bigger packet than server can accept
            payload = b"."*serverMaximumPacketSize
            laclient.publish(topics[0], payload, 0)
            # should get back a disconnect with packet size too big
            response = lacallback.wait_disconnected()
            self.assertEqual(len(lacallback.disconnecteds),
                             0, lacallback.disconnecteds)
            self.assertEqual(response["reasonCode"].getName(),
                             "Packet too large", response["reasonCode"].getName())
        else:
            laclient.disconnect()
            lacallback.wait_disconnected()
        laclient.loop_stop()

        # 1. client max packet size
        maximumPacketSize = 64  # max packet size we want to receive
        connect_properties = Properties(PacketTypes.CONNECT)
        connect_properties.MaximumPacketSize = maximumPacketSize

        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port, properties=connect_properties)
        connack = lacallback.wait_connected()
        laclient.loop_start()

        serverMaximumPacketSize = 2**28-1
        if hasattr(connack["properties"], "MaximumPacketSize"):
            serverMaximumPacketSize = connack["properties"].MaximumPacketSize

        laclient.subscribe(topics[0], qos=2)
        response = lacallback.wait_subscribed()

        # send a small enough packet, should get this one back
        payload = b"."*(int(maximumPacketSize/2))
        laclient.publish(topics[0], payload, 0)
        self.waitfor(lacallback.messages, 1, 3)
        self.assertEqual(len(lacallback.messages), 1, lacallback.messages)

        # send a packet too big to receive
        payload = b"."*maximumPacketSize
        laclient.publish(topics[0], payload, 1)
        self.waitfor(lacallback.messages, 2, 3)
        self.assertEqual(len(lacallback.messages), 1, lacallback.messages)

        laclient.disconnect()
        lacallback.wait_disconnected()
        laclient.loop_stop()

    """
    def test_server_keep_alive(self):
        clientid = 'server keep alive'

        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port)
        connack = lacallback.wait_connected()
        laclient.loop_start()

        self.assertTrue(hasattr(connack["properties"], "ServerKeepAlive"))
        self.assertEqual(connack["properties"].ServerKeepAlive, 60)

        laclient.disconnect()
        lacallback.wait_disconnected()
        laclient.loop_stop()
    """

    def test_will_delay(self):
        # the will message should be received earlier than the session expiry

        clientid = 'will delay'

        will_properties = Properties(PacketTypes.WILLMESSAGE)
        connect_properties = Properties(PacketTypes.CONNECT)

        # set the will delay and session expiry to the same value -
        # then both should occur at the same time
        will_properties.WillDelayInterval = 3  # in seconds
        connect_properties.SessionExpiryInterval = 5

        laclient, lacallback = self.new_client(clientid+" a")
        laclient.will_set(
            topics[0], payload=b"test_will_delay will message", properties=will_properties)
        laclient.connect(host="localhost", port=self._test_broker_port, properties=connect_properties)
        connack = lacallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], False)
        laclient.loop_start()

        lbclient, lbcallback = self.new_client(clientid+" b")
        lbclient.connect(host="localhost", port=self._test_broker_port, properties=connect_properties)
        connack = lbcallback.wait_connected()
        lbclient.loop_start()
        # subscribe to will message topic
        lbclient.subscribe(topics[0], qos=2)
        lbcallback.wait_subscribed()

        # abort client a and wait for the will message
        laclient.loop_stop()
        laclient.socket().close()
        start = time.time()
        while lbcallback.messages == []:
            time.sleep(.1)
        duration = time.time() - start
        self.assertAlmostEqual(duration, 4, delta=1)
        self.assertEqual(lbcallback.messages[0]["message"].topic, topics[0])
        self.assertEqual(
            lbcallback.messages[0]["message"].payload, b"test_will_delay will message")

        lbclient.disconnect()
        lbcallback.wait_disconnected()
        lbclient.loop_stop()

    def test_shared_subscriptions(self):
        clientid = 'shared subscriptions'

        shared_sub_topic = '$share/sharename/' + topic_prefix + 'x'
        shared_pub_topic = topic_prefix + 'x'

        laclient, lacallback = self.new_client(clientid+" a")
        laclient.connect(host="localhost", port=self._test_broker_port)
        connack = lacallback.wait_connected()
        laclient.loop_start()

        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], False)

        laclient.subscribe(
            [(shared_sub_topic, SubscribeOptions(2)), (topics[0], SubscribeOptions(2))])
        response = lacallback.wait_subscribed()

        lbclient, lbcallback = self.new_client(clientid+" b")
        lbclient.connect(host="localhost", port=self._test_broker_port)
        connack = lbcallback.wait_connected()
        lbclient.loop_start()

        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], False)

        lbclient.subscribe(
            [(shared_sub_topic, SubscribeOptions(2)), (topics[0], 2)])
        response = lbcallback.wait_subscribed()

        lacallback.clear()
        lbcallback.clear()

        count = 1
        for i in range(count):
            lbclient.publish(topics[0], "message "+str(i), 0)
        j = 0
        while len(lacallback.messages) + len(lbcallback.messages) < 2*count and j < 20:
            time.sleep(.1)
            j += 1
        time.sleep(1)
        self.assertEqual(len(lacallback.messages), count)
        self.assertEqual(len(lbcallback.messages), count)

        lacallback.clear()
        lbcallback.clear()

        for i in range(count):
            lbclient.publish(shared_pub_topic, "message "+str(i), 0)
        j = 0
        while len(lacallback.messages) + len(lbcallback.messages) < count and j < 20:
            time.sleep(.1)
            j += 1
        time.sleep(1)
        # Each message should only be received once
        self.assertEqual(len(lacallback.messages) +
                         len(lbcallback.messages), count)

        laclient.disconnect()
        lacallback.wait_disconnected()
        laclient.loop_stop()

        lbclient.disconnect()
        lbcallback.wait_disconnected()
        lbclient.loop_stop()


def setData():
    global topics, wildtopics, nosubscribe_topics, topic_prefix
    topics = ("TopicA", "TopicA/B", "Topic/C", "TopicA/C", "/TopicA")
    wildtopics = ("TopicA/+", "+/C", "#", "/#", "/+", "+/+", "TopicA/#")
    nosubscribe_topics = ("test/nosubscribe",)
    topic_prefix = "paho.mqtt.client.mqttv5/"
