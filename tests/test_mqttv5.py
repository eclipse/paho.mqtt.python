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
        return alist.pop(0) if len(alist) > 0 else None

    def wait_connected(self):
        return self.wait(self.connecteds)

    def on_disconnect(self, client, userdata, reasoncode):
        self.disconnecteds.append({"reasonCode": reasoncode})

    def wait_disconnected(self):
        return self.wait(self.disconnecteds)

    def on_message(self, client, userdata, message):
        self.messages.append({"userdata": userdata, "message": message})
        return True

    def published(self, msgid):
        logging.info("published %d", msgid)
        self.publisheds.append(msgid)

    def wait_published(self):
        return self.wait(self.publisheds)

    def on_subscribe(self, client, userdata, mid, properties, reasonCodes):
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
        client.on_unsubscribe = self.unsubscribed
        client.on_message = self.on_message
        client.on_disconnect = self.on_disconnect
        client.on_log = self.on_log


def cleanRetained():
    callback = Callbacks()
    curclient = paho.mqtt.client.Client("clean retained".encode("utf-8"),
                                        protocol=paho.mqtt.client.MQTTv5, clean_session=True)
    curclient.loop_start()
    callback.register(curclient)
    curclient.connect(host=host, port=port)
    response = callback.wait_connected()
    curclient.subscribe("#", options=SubscribeOptions(QoS=0))
    response = callback.wait_subscribed()  # wait for retained messages to arrive
    for message in callback.messages:
        logging.info("deleting retained message for topic", message["message"])
        curclient.publish(message["message"].topic, b"", 0, retain=True)
    curclient.disconnect()
    curclient.loop_stop()
    time.sleep(.1)


def cleanup():
    # clean all client state
    print("clean up starting")
    clientids = ("aclient", "bclient")

    for clientid in clientids:
        curclient = paho.mqtt.client.Client(clientid.encode("utf-8"),
                                            protocol=paho.mqtt.client.MQTTv5, clean_session=True)
        curclient.loop_start()
        curclient.connect(host=host, port=port)
        time.sleep(.1)
        curclient.disconnect()
        time.sleep(.1)
        curclient.loop_stop()

    # clean retained messages
    cleanRetained()
    print("clean up finished")


def usage():
    logging.info(
        """
 -h: --hostname= hostname or ip address of server to run tests against
 -p: --port= port number of server to run tests against
 -z: --zero_length_clientid run zero length clientid test
 -d: --dollar_topics run $ topics test
 -s: --subscribe_failure run subscribe failure test
 -n: --nosubscribe_topic_filter= topic filter name for which subscriptions aren't allowed

""")


class Test(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        setData()
        global callback, callback2, aclient, bclient
        cleanup()

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

    def waitfor(self, queue, depth, limit):
        total = 0
        while len(queue) < depth and total < limit:
            interval = .5
            total += interval
            time.sleep(interval)

    def test_basic(self):
        aclient.connect(host=host, port=port)
        aclient.loop_start()
        response = callback.wait_connected()
        self.assertEqual(response["reasonCode"].getName(), "Success")

        aclient.subscribe(topics[0], options=SubscribeOptions(QoS=2))
        response = callback.wait_subscribed()
        self.assertEqual(response["reasonCodes"].getName(), "Granted QoS 2")

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
        aclient.connect(host=host, port=port)
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
        aclient.subscribe(wildtopics[5], options=SubscribeOptions(QoS=2))
        response = callback.wait_subscribed()
        self.assertEqual(response["reasonCodes"].getName(), "Granted QoS 2")

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

        cleanRetained()

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

        aclient.connect(host=host, port=port, keepalive=2)
        aclient.loop_start()
        response = callback.wait_connected()
        bclient.connect(host=host, port=port)
        bclient.loop_start()
        response = callback2.wait_connected()
        bclient.subscribe(topics[2], qos=2)
        response = callback2.wait_subscribed()
        self.assertEqual(response["reasonCodes"].getName(), "Granted QoS 2")

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

        client0 = paho.mqtt.client.Client(
            protocol=paho.mqtt.client.MQTTv5, clean_start=False)
        callback0.register(client0)
        client0.loop_start()
        client0.connect(host=host, port=port)  # should not be rejected
        response = callback0.wait_connected()
        self.assertEqual(response["reasonCode"].getName(), "Success")
        self.assertTrue(
            len(response["properties"].AssignedClientIdentifier) > 0)
        client0.disconnect()
        client0.loop_stop()

        client0 = paho.mqtt.client.Client(
            protocol=paho.mqtt.client.MQTTv5, clean_start=True)
        callback0.register(client0)
        client0.loop_start()
        client0.connect(host=host, port=port)  # should work
        response = callback0.wait_connected()
        self.assertEqual(response["reasonCode"].getName(), "Success")
        self.assertTrue(
            len(response["properties"].AssignedClientIdentifier) > 0)
        client0.disconnect()
        client0.loop_stop()

        # when we supply a client id, we should not get one assigned
        client0 = paho.mqtt.client.Client(
            "client0", protocol=paho.mqtt.client.MQTTv5, clean_start=True)
        callback0.register(client0)
        client0.loop_start()
        client0.connect(host=host, port=port)  # should work
        response = callback0.wait_connected()
        self.assertEqual(response["reasonCode"].getName(), "Success")
        self.assertFalse(
            hasattr(response["properties"], "AssignedClientIdentifier"))
        client0.disconnect()
        client0.loop_stop()

    def test_offline_message_queueing(self):
        # message queueing for offline clients
        cleanRetained()
        ocallback = Callbacks()
        clientid = "offline message queueing".encode("utf-8")

        oclient = paho.mqtt.client.Client(
            clientid, protocol=paho.mqtt.client.MQTTv5, clean_start=True)
        ocallback.register(oclient)
        connect_properties = Properties(PacketTypes.CONNECT)
        connect_properties.SessionExpiryInterval = 99999
        oclient.loop_start()
        oclient.connect(host=host, port=port, properties=connect_properties)
        response = ocallback.wait_connected()
        oclient.subscribe(wildtopics[5], qos=2)
        response = ocallback.wait_subscribed()
        oclient.disconnect()
        oclient.loop_stop()

        bclient.loop_start()
        bclient.connect(host=host, port=port)
        response = callback2.wait_connected()
        bclient.publish(topics[1], b"qos 0", 0)
        bclient.publish(topics[2], b"qos 1", 1)
        bclient.publish(topics[3], b"qos 2", 2)
        time.sleep(2)
        bclient.disconnect()
        bclient.loop_stop()

        oclient = paho.mqtt.client.Client(
            clientid, protocol=paho.mqtt.client.MQTTv5, clean_start=False)
        ocallback.register(oclient)
        oclient.loop_start()
        oclient.connect(host=host, port=port)
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
            clientid, protocol=paho.mqtt.client.MQTTv5, clean_start=True)
        ocallback.register(oclient)

        oclient.loop_start()
        oclient.connect(host=host, port=port)
        ocallback.wait_connected()
        oclient.subscribe([(wildtopics[6], SubscribeOptions(QoS=2)),
                           (wildtopics[0], SubscribeOptions(QoS=1))])
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
            clientid, protocol=paho.mqtt.client.MQTTv5, clean_start=True)
        ocallback.register(oclient)
        oclient.loop_start()
        oclient.connect(host=host, port=port)
        ocallback.wait_connected()
        oclient.subscribe(nosubscribe_topics[0], qos=2)
        response = ocallback.wait_subscribed()

        self.assertEqual(response["reasonCodes"].getName(), "Unspecified error",
                          "return code should be 0x80 %s" % response["reasonCodes"].getName())
        oclient.disconnect()
        oclient.loop_stop()

    def test_unsubscribe(self):
        callback2.clear()
        bclient.connect(host=host, port=port)
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

        aclient.connect(host=host, port=port)
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

    def new_client(self, clientid, clean_start=True):
        callback = Callbacks()
        client = paho.mqtt.client.Client(
            clientid.encode("utf-8"), protocol=paho.mqtt.client.MQTTv5, clean_start=clean_start)
        callback.register(client)
        client.loop_start()
        return client, callback

    def test_session_expiry(self):
        # no session expiry property == never expire

        connect_properties = Properties(PacketTypes.CONNECT)
        connect_properties.SessionExpiryInterval = 0  # expire immediately

        clientid = "session expiry"

        eclient, ecallback = self.new_client(clientid)

        eclient.connect(host=host, port=port, properties=connect_properties)
        connack = ecallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], False)
        eclient.subscribe(topics[0], qos=2)
        ecallback.wait_subscribed()
        eclient.disconnect()
        ecallback.wait_disconnected()
        eclient.loop_stop()

        fclient, fcallback = self.new_client(clientid, clean_start=False)

        # session should immediately expire
        fclient.connect_async(host=host, port=port,
                              properties=connect_properties)
        connack = fcallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], False)
        fclient.disconnect()
        fcallback.wait_disconnected()

        connect_properties.SessionExpiryInterval = 5

        eclient, ecallback = self.new_client(clientid)

        eclient.connect(host=host, port=port, properties=connect_properties)
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
        fclient, fcallback = self.new_client(clientid, clean_start=False)
        fclient.connect(host=host, port=port, properties=connect_properties)
        connack = fcallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], True)
        fclient.disconnect()
        fcallback.wait_disconnected()
        fclient.loop_stop()

        time.sleep(6)
        # session should not exist
        fclient, fcallback = self.new_client(clientid, clean_start=False)
        fclient.connect(host=host, port=port, properties=connect_properties)
        connack = fcallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], False)
        fclient.disconnect()
        fcallback.wait_disconnected()
        fclient.loop_stop()

        eclient, ecallback = self.new_client(clientid)
        connect_properties.SessionExpiryInterval = 1
        connack = eclient.connect(
            host=host, port=port, properties=connect_properties)
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
        fclient, fcallback = self.new_client(clientid, clean_start=False)
        fclient.connect(host=host, port=port, properties=connect_properties)
        connack = fcallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], True)
        disconnect_properties.SessionExpiryInterval = 0
        fclient.disconnect(properties=disconnect_properties)
        fcallback.wait_disconnected()
        fclient.loop_stop()

        # session should immediately expire
        fclient, fcallback = self.new_client(clientid, clean_start=False)
        fclient.connect(host=host, port=port, properties=connect_properties)
        connack = fcallback.wait_connected()
        self.assertEqual(connack["reasonCode"].getName(), "Success")
        self.assertEqual(connack["flags"]["session present"], False)
        fclient.disconnect()
        fcallback.wait_disconnected()
        fclient.loop_stop()

        fclient.loop_stop()
        eclient.loop_stop()


"""
    def test_user_properties(self):
      callback.clear()
      aclient.connect(host=host, port=port, cleanstart=True)
      aclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2)])
      publish_properties = MQTTV5.Properties(MQTTV5.PacketTypes.PUBLISH)
      publish_properties.UserProperty = ("a", "2")
      publish_properties.UserProperty = ("c", "3")
      aclient.publish(topics[0], b"", 0, retained=False, properties=publish_properties)
      aclient.publish(topics[0], b"", 1, retained=False, properties=publish_properties)
      aclient.publish(topics[0], b"", 2, retained=False, properties=publish_properties)
      while len(callback.messages) < 3:
        time.sleep(.1)
      aclient.disconnect()
      self.assertEqual(len(callback.messages), 3, callback.messages)
      userprops = callback.messages[0][5].UserProperty
      self.assertTrue(userprops in [[("a", "2"), ("c", "3")],[("c", "3"), ("a", "2")]], userprops)
      userprops = callback.messages[1][5].UserProperty
      self.assertTrue(userprops in [[("a", "2"), ("c", "3")],[("c", "3"), ("a", "2")]], userprops)
      userprops = callback.messages[2][5].UserProperty
      self.assertTrue(userprops in [[("a", "2"), ("c", "3")],[("c", "3"), ("a", "2")]], userprops)
      qoss = [callback.messages[i][2] for i in range(3)]
      self.assertTrue(1 in qoss and 2 in qoss and 0 in qoss, qoss)


    def test_payload_format(self):
      callback.clear()
      aclient.connect(host=host, port=port, cleanstart=True)
      aclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2)])
      publish_properties = MQTTV5.Properties(MQTTV5.PacketTypes.PUBLISH)
      publish_properties.PayloadFormatIndicator = 1
      publish_properties.ContentType = "My name"
      aclient.publish(topics[0], b"", 0, retained=False, properties=publish_properties)
      aclient.publish(topics[0], b"", 1, retained=False, properties=publish_properties)
      aclient.publish(topics[0], b"", 2, retained=False, properties=publish_properties)
      while len(callback.messages) < 3:
        time.sleep(.1)
      aclient.disconnect()

      self.assertEqual(len(callback.messages), 3, callback.messages)
      props = callback.messages[0][5]
      self.assertEqual(props.ContentType, "My name", props.ContentType)
      self.assertEqual(props.PayloadFormatIndicator, 1, props.PayloadFormatIndicator)
      props = callback.messages[1][5]
      self.assertEqual(props.ContentType, "My name", props.ContentType)
      self.assertEqual(props.PayloadFormatIndicator, 1, props.PayloadFormatIndicator)
      props = callback.messages[2][5]
      self.assertEqual(props.ContentType, "My name", props.ContentType)
      self.assertEqual(props.PayloadFormatIndicator, 1, props.PayloadFormatIndicator)
      qoss = [callback.messages[i][2] for i in range(3)]
      self.assertTrue(1 in qoss and 2 in qoss and 0 in qoss, qoss)

    def test_publication_expiry(self):
      callback.clear()
      callback2.clear()
      connect_properties = MQTTV5.Properties(MQTTV5.PacketTypes.CONNECT)
      connect_properties.SessionExpiryInterval = 99999
      bclient.connect(host=host, port=port, cleanstart=True, properties=connect_properties)
      bclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2)])
      disconnect_properties = MQTTV5.Properties(MQTTV5.PacketTypes.DISCONNECT)
      disconnect_properties.SessionExpiryInterval = 999999999
      bclient.disconnect(properties = disconnect_properties)

      aclient.connect(host=host, port=port, cleanstart=True)
      publish_properties = MQTTV5.Properties(MQTTV5.PacketTypes.PUBLISH)
      publish_properties.MessageExpiryInterval = 1
      aclient.publish(topics[0], b"qos 1 - expire", 1, retained=False, properties=publish_properties)
      aclient.publish(topics[0], b"qos 2 - expire", 2, retained=False, properties=publish_properties)
      publish_properties.MessageExpiryInterval = 6
      aclient.publish(topics[0], b"qos 1 - don't expire", 1, retained=False, properties=publish_properties)
      aclient.publish(topics[0], b"qos 2 - don't expire", 2, retained=False, properties=publish_properties)

      time.sleep(3)
      bclient.connect(host=host, port=port, cleanstart=False)
      self.waitfor(callback2.messages, 1, 3)
      time.sleep(1)
      self.assertEqual(len(callback2.messages), 2, callback2.messages)
      self.assertTrue(callback2.messages[0][5].MessageExpiryInterval < 6,
                             callback2.messages[0][5].MessageExpiryInterval)
      self.assertTrue(callback2.messages[1][5].MessageExpiryInterval < 6,
                                   callback2.messages[1][5].MessageExpiryInterval)
      aclient.disconnect()

    def test_subscribe_options(self):
      callback.clear()
      callback2.clear()

      # noLocal
      aclient.connect(host=host, port=port, cleanstart=True)
      bclient.connect(host=host, port=port, cleanstart=True)
      aclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2, noLocal=True)])
      self.waitfor(callback.subscribeds, 1, 3)
      bclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2, noLocal=True)])
      self.waitfor(callback.subscribeds, 1, 3)
      aclient.publish(topics[0], b"noLocal test", 1, retained=False)

      self.waitfor(callback2.messages, 1, 3)
      time.sleep(1)

      self.assertEqual(callback.messages, [], callback.messages)
      self.assertEqual(len(callback2.messages), 1, callback2.messages)
      aclient.disconnect()
      bclient.disconnect()

      callback.clear()
      callback2.clear()

      # retainAsPublished
      aclient.connect(host=host, port=port, cleanstart=True)
      aclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2, retainAsPublished=True)])
      self.waitfor(callback.subscribeds, 1, 3)
      aclient.publish(topics[0], b"retain as published false", 1, retained=False)
      aclient.publish(topics[0], b"retain as published true", 1, retained=True)

      self.waitfor(callback.messages, 2, 3)
      time.sleep(1)

      self.assertEqual(len(callback.messages), 2, callback.messages)
      aclient.disconnect()
      self.assertEqual(callback.messages[0][3], False)
      self.assertEqual(callback.messages[1][3], True)

      # retainHandling
      callback.clear()
      aclient.connect(host=host, port=port, cleanstart=True)
      aclient.publish(topics[1], b"qos 0", 0, retained=True)
      aclient.publish(topics[2], b"qos 1", 1, retained=True)
      aclient.publish(topics[3], b"qos 2", 2, retained=True)
      time.sleep(1)
      aclient.subscribe([wildtopics[5]], [MQTTV5.SubscribeOptions(2, retainHandling=1)])
      time.sleep(1)
      self.assertEqual(len(callback.messages), 3)
      qoss = [callback.messages[i][2] for i in range(3)]
      self.assertTrue(1 in qoss and 2 in qoss and 0 in qoss, qoss)
      callback.clear()
      aclient.subscribe([wildtopics[5]], [MQTTV5.SubscribeOptions(2, retainHandling=1)])
      time.sleep(1)
      self.assertEqual(len(callback.messages), 0)
      aclient.disconnect()

      callback.clear()
      aclient.connect(host=host, port=port, cleanstart=True)
      aclient.subscribe([wildtopics[5]], [MQTTV5.SubscribeOptions(2, retainHandling=2)])
      time.sleep(1)
      self.assertEqual(len(callback.messages), 0)
      aclient.subscribe([wildtopics[5]], [MQTTV5.SubscribeOptions(2, retainHandling=2)])
      time.sleep(1)
      self.assertEqual(len(callback.messages), 0)
      aclient.disconnect()

      callback.clear()
      aclient.connect(host=host, port=port, cleanstart=True)
      time.sleep(1)
      aclient.subscribe([wildtopics[5]], [MQTTV5.SubscribeOptions(2, retainHandling=0)])
      time.sleep(1)
      self.assertEqual(len(callback.messages), 3)
      qoss = [callback.messages[i][2] for i in range(3)]
      self.assertTrue(1 in qoss and 2 in qoss and 0 in qoss, qoss)
      callback.clear()
      aclient.subscribe([wildtopics[5]], [MQTTV5.SubscribeOptions(2, retainHandling=0)])
      time.sleep(1)
      self.assertEqual(len(callback.messages), 3)
      qoss = [callback.messages[i][2] for i in range(3)]
      self.assertTrue(1 in qoss and 2 in qoss and 0 in qoss, qoss)
      aclient.disconnect()

      cleanRetained()


    def test_subscribe_identifiers(self):
      callback.clear()
      callback2.clear()

      aclient.connect(host=host, port=port, cleanstart=True)
      sub_properties = MQTTV5.Properties(MQTTV5.PacketTypes.SUBSCRIBE)
      sub_properties.SubscriptionIdentifier = 456789
      aclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2)], properties=sub_properties)
      self.waitfor(callback.subscribeds, 1, 3)

      bclient.connect(host=host, port=port, cleanstart=True)
      sub_properties = MQTTV5.Properties(MQTTV5.PacketTypes.SUBSCRIBE)
      sub_properties.SubscriptionIdentifier = 2
      bclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2)], properties=sub_properties)

      sub_properties.clear()
      sub_properties.SubscriptionIdentifier = 3
      bclient.subscribe([topics[0]+"/#"], [MQTTV5.SubscribeOptions(2)], properties=sub_properties)

      bclient.publish(topics[0], b"sub identifier test", 1, retained=False)

      self.waitfor(callback.messages, 1, 3)
      self.assertEqual(len(callback.messages), 1, callback.messages)
      self.assertEqual(callback.messages[0][5].SubscriptionIdentifier[0], 456789, callback.messages[0][5].SubscriptionIdentifier)
      aclient.disconnect()

      self.waitfor(callback2.messages, 1, 3)
      self.assertEqual(len(callback2.messages), 1, callback2.messages)
      expected_subsids = set([2, 3])
      received_subsids = set(callback2.messages[0][5].SubscriptionIdentifier)
      self.assertEqual(received_subsids, expected_subsids, received_subsids)
      bclient.disconnect()

      callback.clear()
      callback2.clear()

    def test_request_response(self):
      callback.clear()
      callback2.clear()

      aclient.connect(host=host, port=port, cleanstart=True)
      bclient.connect(host=host, port=port, cleanstart=True)
      aclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2, noLocal=True)])
      self.waitfor(callback.subscribeds, 1, 3)

      bclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2, noLocal=True)])
      self.waitfor(callback.subscribeds, 1, 3)

      publish_properties = MQTTV5.Properties(MQTTV5.PacketTypes.PUBLISH)
      publish_properties.ResponseTopic = topics[0]
      publish_properties.CorrelationData = b"334"
      # client a is the requester
      aclient.publish(topics[0], b"request", 1, properties=publish_properties)

      # client b is the responder
      self.waitfor(callback2.messages, 1, 3)
      self.assertEqual(len(callback2.messages), 1, callback2.messages)

      self.assertEqual(len(callback2.messages), 1, callback2.messages)
      self.assertEqual(callback2.messages[0][5].ResponseTopic, topics[0],
                       callback2.messages[0][5])
      self.assertEqual(callback2.messages[0][5].CorrelationData, b"334",
                       callback2.messages[0][5])

      bclient.publish(callback2.messages[0][5].ResponseTopic, b"response", 1,
                      properties=callback2.messages[0][5])

      # client a gets the response
      self.waitfor(callback.messages, 1, 3)
      self.assertEqual(len(callback.messages), 1, callback.messages)

      aclient.disconnect()
      bclient.disconnect()

      callback.clear()
      callback2.clear()

    def test_client_topic_alias(self):
      callback.clear()

      # no server side topic aliases allowed
      connack = aclient.connect(host=host, port=port, cleanstart=True)

      publish_properties = MQTTV5.Properties(MQTTV5.PacketTypes.PUBLISH)
      publish_properties.TopicAlias = 0 # topic alias 0 not allowed
      aclient.publish(topics[0], "topic alias 0", 1, properties=publish_properties)

      # should get back a disconnect with Topic alias invalid
      self.waitfor(callback.disconnects, 1, 2)
      self.assertEqual(len(callback.disconnects), 1, callback.disconnects)
      #print("disconnect", str(callback.disconnects[0]["reasonCode"]))
      #self.assertEqual(callback.disconnects, 1, callback.disconnects)

      connect_properties = MQTTV5.Properties(MQTTV5.PacketTypes.CONNECT)
      connect_properties.TopicAliasMaximum = 0 # server topic aliases not allowed
      connect_properties.SessionExpiryInterval = 99999
      connack = aclient.connect(host=host, port=port, cleanstart=True,
                                           properties=connect_properties)
      clientTopicAliasMaximum = 0
      if hasattr(connack.properties, "TopicAliasMaximum"):
        clientTopicAliasMaximum = connack.properties.TopicAliasMaximum

      if clientTopicAliasMaximum == 0:
        aclient.disconnect()
        return

      aclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2)])
      self.waitfor(callback.subscribeds, 1, 3)

      publish_properties = MQTTV5.Properties(MQTTV5.PacketTypes.PUBLISH)
      publish_properties.TopicAlias = 1
      aclient.publish(topics[0], b"topic alias 1", 1, properties=publish_properties)
      self.waitfor(callback.messages, 1, 3)
      self.assertEqual(len(callback.messages), 1, callback.messages)

      aclient.publish("", b"topic alias 2", 1, properties=publish_properties)
      self.waitfor(callback.messages, 2, 3)
      self.assertEqual(len(callback.messages), 2, callback.messages)

      aclient.disconnect() # should get rid of the topic aliases but not subscriptions

      # check aliases have been deleted
      callback.clear()
      aclient.connect(host=host, port=port, cleanstart=False)

      aclient.publish(topics[0], b"topic alias 3", 1)
      self.waitfor(callback.messages, 1, 3)
      self.assertEqual(len(callback.messages), 1, callback.messages)

      publish_properties = MQTTV5.Properties(MQTTV5.PacketTypes.PUBLISH)
      publish_properties.TopicAlias = 1
      aclient.publish("", b"topic alias 4", 1, properties=publish_properties)

      # should get back a disconnect with Topic alias invalid
      self.waitfor(callback.disconnects, 1, 2)
      self.assertEqual(len(callback.disconnects), 1, callback.disconnects)
      #print("disconnect", str(callback.disconnects[0]["reasonCode"]))
      #self.assertEqual(callback.disconnects, 1, callback.disconnects)

    def test_server_topic_alias(self):
      callback.clear()

      serverTopicAliasMaximum = 1 # server topic alias allowed
      connect_properties = MQTTV5.Properties(MQTTV5.PacketTypes.CONNECT)
      connect_properties.TopicAliasMaximum = serverTopicAliasMaximum
      connack = aclient.connect(host=host, port=port, cleanstart=True,
                                       properties=connect_properties)
      clientTopicAliasMaximum = 0
      if hasattr(connack.properties, "TopicAliasMaximum"):
        clientTopicAliasMaximum = connack.properties.TopicAliasMaximum

      aclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2)])
      self.waitfor(callback.subscribeds, 1, 3)

      for qos in range(3):
         aclient.publish(topics[0], b"topic alias 1", qos)
      self.waitfor(callback.messages, 3, 3)
      self.assertEqual(len(callback.messages), 3, callback.messages)
      aclient.disconnect()

      # first message should set the topic alias
      self.assertTrue(hasattr(callback.messagedicts[0]["properties"], "TopicAlias"), callback.messagedicts[0]["properties"])
      topicalias = callback.messagedicts[0]["properties"].TopicAlias

      self.assertTrue(topicalias > 0)
      self.assertEqual(callback.messagedicts[0]["topicname"], topics[0])

      self.assertEqual(callback.messagedicts[1]["properties"].TopicAlias, topicalias)
      self.assertEqual(callback.messagedicts[1]["topicname"], "")

      self.assertEqual(callback.messagedicts[2]["properties"].TopicAlias, topicalias)
      self.assertEqual(callback.messagedicts[1]["topicname"], "")

      callback.clear()

      serverTopicAliasMaximum = 0 # no server topic alias allowed
      connect_properties = MQTTV5.Properties(MQTTV5.PacketTypes.CONNECT)
      #connect_properties.TopicAliasMaximum = serverTopicAliasMaximum # default is 0
      connack = aclient.connect(host=host, port=port, cleanstart=True,
                                       properties=connect_properties)
      clientTopicAliasMaximum = 0
      if hasattr(connack.properties, "TopicAliasMaximum"):
        clientTopicAliasMaximum = connack.properties.TopicAliasMaximum

      aclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2)])
      self.waitfor(callback.subscribeds, 1, 3)

      for qos in range(3):
         aclient.publish(topics[0], b"topic alias 1", qos)
      self.waitfor(callback.messages, 3, 3)
      self.assertEqual(len(callback.messages), 3, callback.messages)
      aclient.disconnect()

      # No topic aliases
      self.assertFalse(hasattr(callback.messagedicts[0]["properties"], "TopicAlias"), callback.messagedicts[0]["properties"])
      self.assertFalse(hasattr(callback.messagedicts[1]["properties"], "TopicAlias"), callback.messagedicts[1]["properties"])
      self.assertFalse(hasattr(callback.messagedicts[2]["properties"], "TopicAlias"), callback.messagedicts[2]["properties"])

      callback.clear()

      serverTopicAliasMaximum = 0 # no server topic alias allowed
      connect_properties = MQTTV5.Properties(MQTTV5.PacketTypes.CONNECT)
      connect_properties.TopicAliasMaximum = serverTopicAliasMaximum # default is 0
      connack = aclient.connect(host=host, port=port, cleanstart=True,
                                       properties=connect_properties)
      clientTopicAliasMaximum = 0
      if hasattr(connack.properties, "TopicAliasMaximum"):
        clientTopicAliasMaximum = connack.properties.TopicAliasMaximum

      aclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2)])
      self.waitfor(callback.subscribeds, 1, 3)

      for qos in range(3):
         aclient.publish(topics[0], b"topic alias 1", qos)
      self.waitfor(callback.messages, 3, 3)
      self.assertEqual(len(callback.messages), 3, callback.messages)
      aclient.disconnect()

      # No topic aliases
      self.assertFalse(hasattr(callback.messagedicts[0]["properties"], "TopicAlias"), callback.messagedicts[0]["properties"])
      self.assertFalse(hasattr(callback.messagedicts[1]["properties"], "TopicAlias"), callback.messagedicts[1]["properties"])
      self.assertFalse(hasattr(callback.messagedicts[2]["properties"], "TopicAlias"), callback.messagedicts[2]["properties"])


    def test_maximum_packet_size(self):
      callback.clear()

      # 1. server max packet size
      connack = aclient.connect(host=host, port=port, cleanstart=True)
      serverMaximumPacketSize = 2**28-1
      if hasattr(connack.properties, "MaximumPacketSize"):
        serverMaximumPacketSize = connack.properties.MaximumPacketSize

      if serverMaximumPacketSize < 65535:
        # publish bigger packet than server can accept
        payload = b"."*serverMaximumPacketSize
        aclient.publish(topics[0], payload, 0)
        # should get back a disconnect with packet size too big
        self.waitfor(callback.disconnects, 1, 2)
        self.assertEqual(len(callback.disconnects), 1, callback.disconnects)
        self.assertEqual(str(callback.disconnects[0]["reasonCode"]),
          "Packet too large", str(callback.disconnects[0]["reasonCode"]))
      else:
        aclient.disconnect()

      # 1. client max packet size
      maximumPacketSize = 64 # max packet size we want to receive
      connect_properties = MQTTV5.Properties(MQTTV5.PacketTypes.CONNECT)
      connect_properties.MaximumPacketSize = maximumPacketSize
      connack = aclient.connect(host=host, port=port, cleanstart=True,
                                             properties=connect_properties)
      serverMaximumPacketSize = 2**28-1
      if hasattr(connack.properties, "MaximumPacketSize"):
        serverMaximumPacketSize = connack.properties.MaximumPacketSize

      aclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2)])
      self.waitfor(callback.subscribeds, 1, 3)

      # send a small enough packet, should get this one back
      payload = b"."*(int(maximumPacketSize/2))
      aclient.publish(topics[0], payload, 0)
      self.waitfor(callback.messages, 1, 3)
      self.assertEqual(len(callback.messages), 1, callback.messages)

      # send a packet too big to receive
      payload = b"."*maximumPacketSize
      aclient.publish(topics[0], payload, 1)
      self.waitfor(callback.messages, 2, 3)
      self.assertEqual(len(callback.messages), 1, callback.messages)

      aclient.disconnect()

    def test_server_keep_alive(self):
      callback.clear()

      connack = aclient.connect(host=host, port=port, keepalive=120, cleanstart=True)
      self.assertTrue(hasattr(connack.properties, "ServerKeepAlive"))
      self.assertEqual(connack.properties.ServerKeepAlive, 60)

      aclient.disconnect()


    def test_flow_control1(self):
      testcallback = Callbacks()
      # no callback means no background thread, to control receiving
      testclient = mqtt_client.Client("myclientid".encode("utf-8"))

      # set receive maximum - the number of concurrent QoS 1 and 2 messages
      clientReceiveMaximum = 2 # set to low number so we can test
      connect_properties = MQTTV5.Properties(MQTTV5.PacketTypes.CONNECT)
      connect_properties.ReceiveMaximum = clientReceiveMaximum
      connect_properties.SessionExpiryInterval = 0
      connack = testclient.connect(host=host, port=port, cleanstart=True,
                   properties=connect_properties)

      serverReceiveMaximum = 2**16-1 # the default
      if hasattr(connack.properties, "ReceiveMaximum"):
        serverReceiveMaximum = connack.properties.ReceiveMaximum

      receiver = testclient.getReceiver()

      testclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2)])
      receiver.receive(testcallback)
      self.waitfor(testcallback.subscribeds, 1, 3)

      pubs = 0
      for i in range(1, clientReceiveMaximum + 2):
        testclient.publish(topics[0], "message %d" % i, 1)
        pubs += 1

      # get two publishes
      acks = 0
      while True:
        response1 = MQTTV5.unpackPacket(MQTTV5.getPacket(testclient.sock))
        if response1.fh.PacketType == MQTTV5.PacketTypes.PUBLISH:
          break
        self.assertEqual(response1.fh.PacketType, MQTTV5.PacketTypes.PUBACK)
        acks += 1
        del receiver.outMsgs[response1.packetIdentifier]
      self.assertEqual(response1.fh.PacketType, MQTTV5.PacketTypes.PUBLISH)
      self.assertEqual(response1.fh.QoS, 1, response1.fh.QoS)

      while True:
        response2 = MQTTV5.unpackPacket(MQTTV5.getPacket(testclient.sock))
        if response2.fh.PacketType == MQTTV5.PacketTypes.PUBLISH:
          break
        self.assertEqual(response2.fh.PacketType, MQTTV5.PacketTypes.PUBACK)
        acks += 1
        del receiver.outMsgs[response2.packetIdentifier]
      self.assertEqual(response2.fh.PacketType, MQTTV5.PacketTypes.PUBLISH)
      self.assertEqual(response2.fh.QoS, 1, response1.fh.QoS)

      while acks < pubs:
        ack = MQTTV5.unpackPacket(MQTTV5.getPacket(testclient.sock))
        self.assertEqual(ack.fh.PacketType, MQTTV5.PacketTypes.PUBACK)
        acks += 1
        del receiver.outMsgs[ack.packetIdentifier]

      with self.assertRaises(socket.timeout):
        # this should time out because we haven't acknowledged the first one
        response3 = MQTTV5.unpackPacket(MQTTV5.getPacket(testclient.sock))

      # ack the first one
      puback = MQTTV5.Pubacks()
      puback.packetIdentifier = response1.packetIdentifier
      testclient.sock.send(puback.pack())

      # now get the next packet
      response3 = MQTTV5.unpackPacket(MQTTV5.getPacket(testclient.sock))
      self.assertEqual(response3.fh.PacketType, MQTTV5.PacketTypes.PUBLISH)
      self.assertEqual(response3.fh.QoS, 1, response1.fh.QoS)

      # ack the second one
      puback.packetIdentifier = response2.packetIdentifier
      testclient.sock.send(puback.pack())

      # ack the third one
      puback.packetIdentifier = response3.packetIdentifier
      testclient.sock.send(puback.pack())

      testclient.disconnect()

    def test_flow_control2(self):
      testcallback = Callbacks()
      # no callback means no background thread, to control receiving
      testclient = mqtt_client.Client("myclientid".encode("utf-8"))

      # get receive maximum - the number of concurrent QoS 1 and 2 messages
      connect_properties = MQTTV5.Properties(MQTTV5.PacketTypes.CONNECT)
      connect_properties.SessionExpiryInterval = 0
      connack = testclient.connect(host=host, port=port, cleanstart=True)

      serverReceiveMaximum = 2**16-1 # the default
      if hasattr(connack.properties, "ReceiveMaximum"):
        serverReceiveMaximum = connack.properties.ReceiveMaximum

      receiver = testclient.getReceiver()

      # send number of messages to exceed receive maximum
      qos = 2
      pubs = 0
      for i in range(1, serverReceiveMaximum + 2):
        testclient.publish(topics[0], "message %d" % i, qos)
        pubs += 1

      # should get disconnected...
      while testcallback.disconnects == []:
        receiver.receive(testcallback)
      self.waitfor(testcallback.disconnects, 1, 1)
      self.assertEqual(len(testcallback.disconnects), 1, len(testcallback.disconnects))
      self.assertEqual(testcallback.disconnects[0]["reasonCode"].value, 147,
                       testcallback.disconnects[0]["reasonCode"].value)

    def test_will_delay(self):
      #the will message should be received earlier than the session expiry

      callback.clear()
      callback2.clear()

      will_properties = MQTTV5.Properties(MQTTV5.PacketTypes.WILLMESSAGE)
      connect_properties = MQTTV5.Properties(MQTTV5.PacketTypes.CONNECT)

      # set the will delay and session expiry to the same value -
      # then both should occur at the same time
      will_properties.WillDelayInterval = 3 # in seconds
      connect_properties.SessionExpiryInterval = 5

      connack = aclient.connect(host=host, port=port, cleanstart=True, properties=connect_properties,
        willProperties=will_properties, willFlag=True, willTopic=topics[0], willMessage=b"test_will_delay will message")
      self.assertEqual(connack.reasonCode.getName(), "Success")
      self.assertEqual(connack.sessionPresent, False)

      connack = bclient.connect(host=host, port=port, cleanstart=True)
      bclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2)]) # subscribe to will message topic
      self.waitfor(callback2.subscribeds, 1, 3)

      # terminate client a and wait for the will message
      aclient.terminate()
      start = time.time()
      while callback2.messages == []:
        time.sleep(.1)
      duration = time.time() - start
      #print(duration)
      self.assertAlmostEqual(duration, 4, delta=1)
      self.assertEqual(callback2.messages[0][0], topics[0])
      self.assertEqual(callback2.messages[0][1], b"test_will_delay will message")

      aclient.disconnect()
      bclient.disconnect()

      callback.clear()
      callback2.clear()

      # if session expiry is less than will delay then session expiry is used
      will_properties.WillDelayInterval = 5 # in seconds
      connect_properties.SessionExpiryInterval = 0

      connack = aclient.connect(host=host, port=port, cleanstart=True, properties=connect_properties,
        willProperties=will_properties, willFlag=True, willTopic=topics[0], willMessage=b"test_will_delay will message")
      self.assertEqual(connack.reasonCode.getName(), "Success")
      self.assertEqual(connack.sessionPresent, False)

      connack = bclient.connect(host=host, port=port, cleanstart=True)
      bclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2)]) # subscribe to will message topic
      self.waitfor(callback2.subscribeds, 1, 3)

      # terminate client a and wait for the will message
      aclient.terminate()
      start = time.time()
      while callback2.messages == []:
        time.sleep(.1)
      duration = time.time() - start
      #print(duration)
      self.assertAlmostEqual(duration, 1, delta=1)
      self.assertEqual(callback2.messages[0][0], topics[0])
      self.assertEqual(callback2.messages[0][1], b"test_will_delay will message")

      aclient.disconnect()
      bclient.disconnect()

      callback.clear()
      callback2.clear()

            # if session expiry is less than will delay then session expiry is used
      will_properties.WillDelayInterval = 5 # in seconds
      connect_properties.SessionExpiryInterval = 2

      connack = aclient.connect(host=host, port=port, cleanstart=True, properties=connect_properties,
        willProperties=will_properties, willFlag=True, willTopic=topics[0], willMessage=b"test_will_delay will message")
      self.assertEqual(connack.reasonCode.getName(), "Success")
      self.assertEqual(connack.sessionPresent, False)

      connack = bclient.connect(host=host, port=port, cleanstart=True)
      bclient.subscribe([topics[0]], [MQTTV5.SubscribeOptions(2)]) # subscribe to will message topic
      self.waitfor(callback2.subscribeds, 1, 3)

      # terminate client a and wait for the will message
      aclient.terminate()
      start = time.time()
      while callback2.messages == []:
        time.sleep(.1)
      duration = time.time() - start
      #print(duration)
      self.assertAlmostEqual(duration, 3, delta=1)
      self.assertEqual(callback2.messages[0][0], topics[0])
      self.assertEqual(callback2.messages[0][1], b"test_will_delay will message")

      aclient.disconnect()
      bclient.disconnect()

      callback.clear()
      callback2.clear()

    def test_shared_subscriptions(self):

      callback.clear()
      callback2.clear()
      shared_sub_topic = '$share/sharename/' + topic_prefix + 'x'
      shared_pub_topic = topic_prefix + 'x'

      connack = aclient.connect(host=host, port=port, cleanstart=True)
      self.assertEqual(connack.reasonCode.getName(), "Success")
      self.assertEqual(connack.sessionPresent, False)
      aclient.subscribe([shared_sub_topic, topics[0]], [MQTTV5.SubscribeOptions(2)]*2) 
      self.waitfor(callback.subscribeds, 1, 3)

      connack = bclient.connect(host=host, port=port, cleanstart=True)
      self.assertEqual(connack.reasonCode.getName(), "Success")
      self.assertEqual(connack.sessionPresent, False)
      bclient.subscribe([shared_sub_topic, topics[0]], [MQTTV5.SubscribeOptions(2)]*2) 
      self.waitfor(callback2.subscribeds, 1, 3)

      callback.clear()
      callback2.clear()

      count = 1
      for i in range(count):
        bclient.publish(topics[0], "message "+str(i), 0)
      j = 0
      while len(callback.messages) + len(callback2.messages) < 2*count and j < 20:
        time.sleep(.1)
        j += 1
      time.sleep(1)
      self.assertEqual(len(callback.messages), count)
      self.assertEqual(len(callback2.messages), count)

      callback.clear()
      callback2.clear()

      for i in range(count):
        bclient.publish(shared_pub_topic, "message "+str(i), 0)
      j = 0
      while len(callback.messages) + len(callback2.messages) < count and j < 20:
        time.sleep(.1)
        j += 1
      time.sleep(1)
      # Each message should only be received once
      self.assertEqual(len(callback.messages) + len(callback2.messages), count)

      aclient.disconnect()
      bclient.disconnect()

"""


def setData():
    global topics, wildtopics, nosubscribe_topics, host, port
    host = "paho8181.cloudapp.net"
    port = 1883
    topics = ("TopicA", "TopicA/B", "Topic/C", "TopicA/C", "/TopicA")
    wildtopics = ("TopicA/+", "+/C", "#", "/#", "/+", "+/+", "TopicA/#")
    nosubscribe_topics = ("test/nosubscribe",)


if __name__ == "__main__":
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "h:p:vzdsn:",
                                       ["help", "hostname=", "port=", "iterations="])
    except getopt.GetoptError as err:
        # will print something like "option -a not recognized"
        logging.info(err)
        usage()
        sys.exit(2)

    iterations = 1

    global topics, wildtopics, nosubscribe_topics, host, topic_prefix
    topic_prefix = "client_test5/"
    topics = [topic_prefix+topic for topic in ["TopicA",
                                               "TopicA/B", "Topic/C", "TopicA/C", "/TopicA"]]
    wildtopics = [topic_prefix+topic for topic in ["TopicA/+",
                                                   "+/C", "#", "/#", "/+", "+/+", "TopicA/#"]]
    print(wildtopics)
    nosubscribe_topics = ("test/nosubscribe",)

    host = "localhost"
    port = 1883
    for o, a in opts:
        if o in ("--help"):
            usage()
            sys.exit()
        elif o in ("-n", "--nosubscribe_topic_filter"):
            nosubscribe_topic_filter = a
        elif o in ("-h", "--hostname"):
            host = a
        elif o in ("-p", "--port"):
            port = int(a)
            sys.argv.remove(
                "-p") if "-p" in sys.argv else sys.argv.remove("--port")
            sys.argv.remove(a)
        elif o in ("--iterations"):
            iterations = int(a)

    root = logging.getLogger()
    root.setLevel(logging.ERROR)

    logging.info("hostname %s port %d", host, port)
    print("argv", sys.argv)
    for i in range(iterations):
        unittest.main()
