import pytest

from paho.mqtt.subscribe import simple, callback
from paho.mqtt.client import MQTTv5


class TestSimple(object):
    def test_invalid_protocol(self):
        with pytest.raises(NotImplementedError):
            simple("test/topic", protocol=MQTTv5)


class TestCallback(object):
    def test_invalid_protocol(self):
        # Define a dummy callback
        def on_message(client, userdata, message):
            raise RuntimeError("This shouldn't be called")

        with pytest.raises(NotImplementedError):
            callback(on_message, ["test/topic"], protocol=MQTTv5)
