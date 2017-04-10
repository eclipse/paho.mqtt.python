import pytest

import paho.mqtt.client as mqtt


@pytest.mark.parametrize("sub,topic", [
    ("foo/bar", "foo/bar"),
    ("foo/+", "foo/bar"),
    ("foo/+/baz", "foo/bar/baz"),
    ("foo/+/#", "foo/bar/baz"),
    ("A/B/+/#", "A/B/B/C"),
    ("#", "foo/bar/baz"),
    ("#", "/foo/bar"),
    ("/#", "/foo/bar"),
    ("$SYS/bar", "$SYS/bar"),
])
def test_matching(sub, topic):
    assert mqtt.topic_matches_sub(sub, topic)


@pytest.mark.parametrize("sub,topic", [
    ("test/6/#", "test/3"),
    ("foo/bar", "foo"),
    ("foo/+", "foo/bar/baz"),
    ("foo/+/baz", "foo/bar/bar"),
    ("foo/+/#", "fo2/bar/baz"),
    ("/#", "foo/bar"),
    ("#", "$SYS/bar"),
    ("$BOB/bar", "$SYS/bar"),
])
def test_not_matching(sub, topic):
    assert not mqtt.topic_matches_sub(sub, topic)
