"""
*******************************************************************
  Copyright (c) 2017, 2018 IBM Corp.

  All rights reserved. This program and the accompanying materials
  are made available under the terms of the Eclipse Public License v1.0
  and Eclipse Distribution License v1.0 which accompany this distribution.

  The Eclipse Public License is available at
     http://www.eclipse.org/legal/epl-v10.html
  and the Eclipse Distribution License is available at
    http://www.eclipse.org/org/documents/edl-v10.php.

  Contributors:
     Ian Craggs - initial implementation and/or documentation
*******************************************************************
"""

from .packettypes import PacketTypes


class ReasonCodes:
    """
      The reason code used in MQTT V5.0

    """

    def __getName__(self, packetType, identifier):
        """
        used when displaying the reason code
        """
        assert identifier in self.names.keys(), identifier
        names = self.names[identifier]
        namelist = [name for name in names.keys() if packetType in names[name]]
        assert len(namelist) == 1
        return namelist[0]

    def getId(self, name):
        """
        used when setting the reason code for a packetType
        check that only valid codes for the packet are set
        """
        identifier = None
        for code in self.names.keys():
            if name in self.names[code].keys():
                if self.packetType in self.names[code][name]:
                    identifier = code
                break
        assert identifier != None, name
        return identifier

    def set(self, name):
        self.value = self.getId(name)

    def unpack(self, buffer):
        name = self.__getName__(self.packetType, buffer[0])
        self.value = self.getId(name)
        return 1

    def getName(self):
        return self.__getName__(self.packetType, self.value)

    def __str__(self):
        return self.getName()

    def json(self):
        return self.getName()

    def pack(self):
        return bytearray([self.value])

    def __init__(self, packetType, aName="Success", identifier=-1):
        self.packetType = packetType
        self.names = {
            0: {"Success": [PacketTypes.CONNACK, PacketTypes.PUBACK,
                            PacketTypes.PUBREC, PacketTypes.PUBREL, PacketTypes.PUBCOMP,
                            PacketTypes.UNSUBACK, PacketTypes.AUTH],
                "Normal disconnection": [PacketTypes.DISCONNECT],
                "Granted QoS 0": [PacketTypes.SUBACK]},
            1: {"Granted QoS 1": [PacketTypes.SUBACK]},
            2: {"Granted QoS 2": [PacketTypes.SUBACK]},
            4: {"Disconnect with will message": [PacketTypes.DISCONNECT]},
            16: {"No matching subscribers":
                 [PacketTypes.PUBACK, PacketTypes.PUBREC]},
            17: {"No subscription found": [PacketTypes.UNSUBACK]},
            24: {"Continue authentication": [PacketTypes.AUTH]},
            25: {"Re-authenticate": [PacketTypes.AUTH]},
            128: {"Unspecified error": [PacketTypes.CONNACK, PacketTypes.PUBACK,
                                        PacketTypes.PUBREC, PacketTypes.SUBACK, PacketTypes.UNSUBACK,
                                        PacketTypes.DISCONNECT], },
            129: {"Malformed packet":
                  [PacketTypes.CONNACK, PacketTypes.DISCONNECT]},
            130: {"Protocol error":
                  [PacketTypes.CONNACK, PacketTypes.DISCONNECT]},
            131: {"Implementation specific error": [PacketTypes.CONNACK,
                                                    PacketTypes.PUBACK, PacketTypes.PUBREC, PacketTypes.SUBACK,
                                                    PacketTypes.UNSUBACK, PacketTypes.DISCONNECT], },
            132: {"Unsupported protocol version": [PacketTypes.CONNACK]},
            133: {"Client identifier not valid": [PacketTypes.CONNACK]},
            134: {"Bad user name or password": [PacketTypes.CONNACK]},
            135: {"Not authorized": [PacketTypes.CONNACK, PacketTypes.PUBACK,
                                     PacketTypes.PUBREC, PacketTypes.SUBACK, PacketTypes.UNSUBACK,
                                     PacketTypes.DISCONNECT], },
            136: {"Server unavailable": [PacketTypes.CONNACK]},
            137: {"Server busy": [PacketTypes.CONNACK, PacketTypes.DISCONNECT]},
            138: {"Banned": [PacketTypes.CONNACK]},
            139: {"Server shutting down": [PacketTypes.DISCONNECT]},
            140: {"Bad authentication method":
                  [PacketTypes.CONNACK, PacketTypes.DISCONNECT]},
            141: {"Keep alive timeout": [PacketTypes.DISCONNECT]},
            142: {"Session taken over": [PacketTypes.DISCONNECT]},
            143: {"Topic filter invalid":
                  [PacketTypes.SUBACK, PacketTypes.UNSUBACK, PacketTypes.DISCONNECT]},
            144: {"Topic name invalid":
                  [PacketTypes.CONNACK, PacketTypes.PUBACK,
                   PacketTypes.PUBREC, PacketTypes.DISCONNECT]},
            145: {"Packet identifier in use":
                  [PacketTypes.PUBACK, PacketTypes.PUBREC,
                   PacketTypes.SUBACK, PacketTypes.UNSUBACK]},
            146: {"Packet identifier not found":
                  [PacketTypes.PUBREL, PacketTypes.PUBCOMP]},
            147: {"Receive maximum exceeded": [PacketTypes.DISCONNECT]},
            148: {"Topic alias invalid": [PacketTypes.DISCONNECT]},
            149: {"Packet too large": [PacketTypes.CONNACK, PacketTypes.DISCONNECT]},
            150: {"Message rate too high": [PacketTypes.DISCONNECT]},
            151: {"Quota exceeded": [PacketTypes.CONNACK, PacketTypes.PUBACK,
                                     PacketTypes.PUBREC, PacketTypes.SUBACK, PacketTypes.DISCONNECT], },
            152: {"Administrative action": [PacketTypes.DISCONNECT]},
            153: {"Payload format invalid":
                  [PacketTypes.PUBACK, PacketTypes.PUBREC, PacketTypes.DISCONNECT]},
            154: {"Retain not supported":
                  [PacketTypes.CONNACK, PacketTypes.DISCONNECT]},
            155: {"QoS not supported":
                  [PacketTypes.CONNACK, PacketTypes.DISCONNECT]},
            156: {"Use another server":
                  [PacketTypes.CONNACK, PacketTypes.DISCONNECT]},
            157: {"Server moved":
                  [PacketTypes.CONNACK, PacketTypes.DISCONNECT]},
            158: {"Shared subscription not supported":
                  [PacketTypes.SUBACK, PacketTypes.DISCONNECT]},
            159: {"Connection rate exceeded":
                  [PacketTypes.CONNACK, PacketTypes.DISCONNECT]},
            160: {"Maximum connect time":
                  [PacketTypes.DISCONNECT]},
            161: {"Subscription identifiers not supported":
                  [PacketTypes.SUBACK, PacketTypes.DISCONNECT]},
            162: {"Wildcard subscription not supported":
                  [PacketTypes.SUBACK, PacketTypes.DISCONNECT]},
        }
        if identifier == -1:
            self.set(aName)
        else:
            self.value = identifier
            self.getName()  # check it's good