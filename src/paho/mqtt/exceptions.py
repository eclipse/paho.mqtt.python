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


class MQTTException(Exception):
    """
    MQTT Exception.
    """


class MalformedPacket(MQTTException):
    """
    Malformed Packet exception.
    """
