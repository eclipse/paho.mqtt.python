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

import time
import threading
from .constants import MQTT_ERR_QUEUE_SIZE, MQTT_ERR_AGAIN, error_string

class MQTTMessageInfo():
    """
    This is a class returned from Client.publish() and can be used to find
    out the mid of the message that was published, and to determine whether the
    message has been published, and/or wait until it is published.
    """

    __slots__ = "mid", "_published", "_condition", "rc", "_iterpos"

    def __init__(self, mid):
        """
        Constructor.
        """
        self.mid = mid
        self._published = False
        self._condition = threading.Condition()
        self.rc = 0
        self._iterpos = 0

    def __str__(self):
        """
        Human readable string.
        """

        return str((self.rc, self.mid))

    def __iter__(self):
        """
        Iterator.
        """

        self._iterpos = 0
        return self

    def __next__(self):
        """
        Get next iteration.
        """

        return self.next()

    def next(self):
        """
        Get next iteration.
        """

        if self._iterpos == 0:
            self._iterpos = 1
            return self.rc
        if self._iterpos == 1:
            self._iterpos = 2
            return self.mid
        raise StopIteration

    def __getitem__(self, index):
        """
        Get item.
        """

        if index == 0:
            return self.rc
        if index == 1:
            return self.mid
        raise IndexError("index out of range")

    def _set_as_published(self):
        """
        Set published flag.
        """

        with self._condition:
            self._published = True
            self._condition.notify()

    def wait_for_publish(self, timeout=None):
        """
        Block until the message associated with this object is published, or
        until the timeout occurs. If timeout is None, this will never time out.
        Set timeout to a positive number of seconds, e.g. 1.2, to enable the
        timeout.

        Raises ValueError if the message was not queued due to the outgoing
        queue being full.

        Raises RuntimeError if the message was not published for another
        reason.
        """

        if self.rc == MQTT_ERR_QUEUE_SIZE:
            raise ValueError("Message is not queued due to ERR_QUEUE_SIZE")
        if self.rc == MQTT_ERR_AGAIN:
            pass
        elif self.rc > 0:
            raise RuntimeError(f"Message publish failed: {error_string(self.rc)}")

        timeout_time = None if timeout is None else time.time() + timeout
        timeout_tenth = None if timeout is None else timeout / 10.0

        def timed_out():
            return False if timeout is None else time.time() > timeout_time

        with self._condition:
            while not self._published and not timed_out():
                self._condition.wait(timeout_tenth)

    def is_published(self):
        """
        Returns True if the message associated with this object has been
        published, else returns False.
        """

        if self.rc == MQTT_ERR_QUEUE_SIZE:
            raise ValueError("Message is not queued due to ERR_QUEUE_SIZE")
        if self.rc == MQTT_ERR_AGAIN:
            pass
        elif self.rc > 0:
            raise RuntimeError(f"Message publish failed: {error_string(self.rc)}")

        with self._condition:
            return self._published
