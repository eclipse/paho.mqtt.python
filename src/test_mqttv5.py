import time, traceback

import paho.mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.reasoncodes import ReasonCodes
from paho.mqtt.subscribeoptions import SubscribeOptions
from paho.mqtt.packettypes import PacketTypes
import paho.mqtt.client

print(paho.mqtt.__version__)

connected = False
disconnected = False

def on_unsubscribe(client, userdata, mid, properties, reasoncodes):
    print("unsubscribed", userdata, mid, properties, reasoncodes)

    try:
        disc_props = Properties(PacketTypes.DISCONNECT)
        disc_props.ReasonString = "disc reason"
        client.disconnect(ReasonCodes(PacketTypes.DISCONNECT, aName="Normal disconnection"),
                        properties=disc_props)
    except:
        traceback.print_exc()

def on_message(client, userdata, message):
    print('on_message', userdata, "properties:", message.properties, message.payload)

    unsubs_props = Properties(PacketTypes.UNSUBSCRIBE)
    unsubs_props.UserProperty = ("unsub_name", "unsub_value")
    client.unsubscribe('a', properties=unsubs_props)

def on_subscribe(client, userdata, mid, properties, reasoncodes):
    print("subscribed", userdata, mid, properties, reasoncodes)

    client.publish("a", payload="test", qos=0, retain=False, properties=None)

def on_disconnect(client, userdata, rc):
    print("on_disconnect")
    global disconnected
    disconnected = True

def on_connect(client, userdata, flags, result, properties):
    print("connected", userdata, flags, result, properties)
    global connected
    connected = True

    subs_props = Properties(PacketTypes.SUBSCRIBE)
    subs_props.SubscriptionIdentifier = 3
    sub_opts = SubscribeOptions(retainHandling=2)
    sub_opts.QoS = 2
    client.subscribe('a', options=sub_opts, properties=subs_props)


k = paho.mqtt.client.Client(protocol=paho.mqtt.client.MQTTv5)
k.user_data_set("mine")

k.on_connect = on_connect
k.on_subscribe = on_subscribe
k.on_unsubscribe = on_unsubscribe
k.on_message = on_message
k.on_disconnect = on_disconnect

will_props = Properties(PacketTypes.WILLMESSAGE)
will_props.UserProperty = ("name", "value")
will_props.UserProperty = ("name1", "value2")
k.will_set("will_topic", payload="will message", properties=will_props)

conn_props = Properties(PacketTypes.CONNECT)
conn_props.UserProperty = ("name", "value")
conn_props.UserProperty = ("name1", "value2")
k.connect("localhost", properties=conn_props)

k.loop_start()

while not connected:
    time.sleep(.1)

while not disconnected:
    time.sleep(.1)


