import pytest

from paho.mqtt.client import MQTTv5
from paho.mqtt.publish import multiple, single


class TestSingle(object):
    def test_invalid_protocol(self):
        with pytest.raises(NotImplementedError):
            single("test/topic", protocol=MQTTv5)


class TestMultiple(object):
    def test_invalid_protocol(self):
        with pytest.raises(NotImplementedError):
            multiple([{"topic": "test/topic"}], protocol=MQTTv5)
