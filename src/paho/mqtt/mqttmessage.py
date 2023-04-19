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


from .constants import MQTT_MS_INVALID
from .mqttmessageinfo import MQTTMessageInfo

class MQTTMessage():
    """
    This is a class that describes an incoming or outgoing message. It is
    passed to the on_message callback as the message parameter.

    Members:

    topic : String. topic that the message was published on.
    payload : Bytes/Byte array. the message payload.
    qos : Integer. The message Quality of Service 0, 1 or 2.
    retain : Boolean. If true, the message is a retained message and not fresh.
    mid : Integer. The message id.
    properties: Properties class. In MQTT v5.0, the properties associated with the message.
    """

    __slots__ = (
        "timestamp",
        "state",
        "dup",
        "mid",
        "_topic",
        "payload",
        "qos",
        "retain",
        "info",
        "properties",
    )

    def __init__(self, mid=0, topic=b""):
        """
        Constructor.
        """
        self.timestamp = 0
        self.state = MQTT_MS_INVALID
        self.dup = False
        self.mid = mid
        self._topic = topic
        self.payload = b""
        self.qos = 0
        self.retain = False
        self.info = MQTTMessageInfo(mid)

    def __eq__(self, other):
        """
        Override the default Equals behavior.
        """

        if isinstance(other, self.__class__):
            return self.mid == other.mid
        return False

    def __ne__(self, other):
        """
        Define a non-equality test.
        """

        return not self.__eq__(other)

    @property
    def topic(self):
        """
        Getter for topic.
        """

        return self._topic.decode("utf-8")

    @topic.setter
    def topic(self, value):
        """
        Setter for topic.
        """

        self._topic = value
