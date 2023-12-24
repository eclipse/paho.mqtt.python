import paho.mqtt.client as mqtt
import pytest

from tests.paho_test import ssl


@pytest.mark.skipif(ssl is None, reason="no ssl module")
def test_08_ssl_bad_cacert():
    with pytest.raises(IOError):
        mqttc = mqtt.Client("08-ssl-bad-cacert")
        mqttc.tls_set("this/file/doesnt/exist")
