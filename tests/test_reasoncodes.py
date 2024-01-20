from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.reasoncodes import ReasonCodes


class TestReasonCode:
    def test_equality(self):
        rc_success = ReasonCodes(PacketTypes.CONNACK, "Success")
        assert rc_success == 0
        assert rc_success == "Success"
        assert rc_success != "Protocol error"
        assert rc_success == ReasonCodes(PacketTypes.CONNACK, "Success")

        rc_protocol_error = ReasonCodes(PacketTypes.CONNACK, "Protocol error")
        assert rc_protocol_error == 130
        assert rc_protocol_error == "Protocol error"
        assert rc_protocol_error != "Success"
        assert rc_protocol_error == ReasonCodes(PacketTypes.CONNACK, "Protocol error")

    def test_comparison(self):
        rc_success = ReasonCodes(PacketTypes.CONNACK, "Success")
        rc_protocol_error = ReasonCodes(PacketTypes.CONNACK, "Protocol error")

        assert not rc_success > 0
        assert rc_protocol_error > 0
        assert not rc_success != 0
        assert rc_protocol_error != 0
