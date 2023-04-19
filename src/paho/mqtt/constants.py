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

import logging

MQTT_CLIENT = 0
MQTT_BRIDGE = 1
MQTTV31 = 3
MQTTV311 = 4
MQTTV5 = 5

# For MQTT V5, use the clean start flag only on the first successful connect
MQTT_CLEAN_START_FIRST_ONLY = 3

SOCKPAIR_DATA = b"0"

# Message types
CONNECT = 0x10
CONNACK = 0x20
PUBLISH = 0x30
PUBACK = 0x40
PUBREC = 0x50
PUBREL = 0x60
PUBCOMP = 0x70
SUBSCRIBE = 0x80
SUBACK = 0x90
UNSUBSCRIBE = 0xA0
UNSUBACK = 0xB0
PINGREQ = 0xC0
PINGRESP = 0xD0
DISCONNECT = 0xE0
AUTH = 0xF0

# Log levels
MQTT_LOG_INFO = 0x01
MQTT_LOG_NOTICE = 0x02
MQTT_LOG_WARNING = 0x04
MQTT_LOG_ERR = 0x08
MQTT_LOG_DEBUG = 0x10
LOGGING_LEVEL = {
    MQTT_LOG_DEBUG: logging.DEBUG,
    MQTT_LOG_INFO: logging.INFO,
    MQTT_LOG_NOTICE: logging.INFO,  # This has no direct equivalent level
    MQTT_LOG_WARNING: logging.WARNING,
    MQTT_LOG_ERR: logging.ERROR,
}

# Connection state
MQTT_CS_NEW = 0
MQTT_CS_CONNECTED = 1
MQTT_CS_DISCONNECTING = 2
MQTT_CS_CONNECT_ASYNC = 3

# Message state
MQTT_MS_INVALID = 0
MQTT_MS_PUBLISH = 1
MQTT_MS_WAIT_FOR_PUBACK = 2
MQTT_MS_WAIT_FOR_PUBREC = 3
MQTT_MS_RESEND_PUBREL = 4
MQTT_MS_WAIT_FOR_PUBREL = 5
MQTT_MS_RESEND_PUBCOMP = 6
MQTT_MS_WAIT_FOR_PUBCOMP = 7
MQTT_MS_SEND_PUBREC = 8
MQTT_MS_QUEUED = 9

# Error values
MQTT_ERR_AGAIN = -1
MQTT_ERR_SUCCESS = 0
MQTT_ERR_NOMEM = 1
MQTT_ERR_PROTOCOL = 2
MQTT_ERR_INVAL = 3
MQTT_ERR_NO_CONN = 4
MQTT_ERR_CONN_REFUSED = 5
MQTT_ERR_NOT_FOUND = 6
MQTT_ERR_CONN_LOST = 7
MQTT_ERR_TLS = 8
MQTT_ERR_PAYLOAD_SIZE = 9
MQTT_ERR_NOT_SUPPORTED = 10
MQTT_ERR_AUTH = 11
MQTT_ERR_ACL_DENIED = 12
MQTT_ERR_UNKNOWN = 13
MQTT_ERR_ERRNO = 14
MQTT_ERR_QUEUE_SIZE = 15
MQTT_ERR_KEEPALIVE = 16

# CONNACK codes
CONNACK_ACCEPTED = 0
CONNACK_REFUSED_PROTOCOL_VERSION = 1
CONNACK_REFUSED_IDENTIFIER_REJECTED = 2
CONNACK_REFUSED_SERVER_UNAVAILABLE = 3
CONNACK_REFUSED_BAD_USERNAME_PASSWORD = 4
CONNACK_REFUSED_NOT_AUTHORIZED = 5

ERR_STRINGS = {
    MQTT_ERR_SUCCESS: "No error.",
    MQTT_ERR_NOMEM: "Out of memory.",
    MQTT_ERR_PROTOCOL: "A network protocol error occurred when communicating with the broker.",
    MQTT_ERR_INVAL: "Invalid function arguments provided.",
    MQTT_ERR_NO_CONN: "The client is not currently connected.",
    MQTT_ERR_CONN_REFUSED: "The connection was refused.",
    MQTT_ERR_NOT_FOUND: "Message not found (internal error).",
    MQTT_ERR_CONN_LOST: "The connection was lost.",
    MQTT_ERR_TLS: "A TLS error occurred.",
    MQTT_ERR_PAYLOAD_SIZE: "Payload too large.",
    MQTT_ERR_NOT_SUPPORTED: "This feature is not supported.",
    MQTT_ERR_AUTH: "Authorisation failed.",
    MQTT_ERR_ACL_DENIED: "Access denied by ACL.",
    MQTT_ERR_UNKNOWN: "Unknown error.",
    MQTT_ERR_ERRNO: "Error defined by errno.",
    MQTT_ERR_QUEUE_SIZE: "Message queue full.",
    MQTT_ERR_KEEPALIVE: "Client or broker did not communicate in the keepalive interval.",
}

CONNACK_STRINGS = {
    CONNACK_ACCEPTED: "Connection Accepted.",
    CONNACK_REFUSED_PROTOCOL_VERSION: "Connection Refused: unacceptable protocol version.",
    CONNACK_REFUSED_IDENTIFIER_REJECTED: "Connection Refused: identifier rejected.",
    CONNACK_REFUSED_SERVER_UNAVAILABLE: "Connection Refused: broker unavailable.",
    CONNACK_REFUSED_BAD_USERNAME_PASSWORD: "Connection Refused: bad user name or password.",
    CONNACK_REFUSED_NOT_AUTHORIZED: "Connection Refused: not authorised.",
}


def error_string(mqtt_errno):
    """
    Return the error string associated with an mqtt error number.
    """

    return ERR_STRINGS.get(mqtt_errno, "Unknown error.")


def connack_string(connack_code):
    """
    Return the string associated with a CONNACK result.
    """

    return CONNACK_STRINGS.get(connack_code, "Connection Refused: unknown reason.")
