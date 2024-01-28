# Types and enums

### *class* paho.mqtt.enums.CallbackAPIVersion(value, names=None, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

Defined the arguments passed to all user-callback.

See each callbacks for details: [`on_connect`](client.md#paho.mqtt.client.Client.on_connect), [`on_connect_fail`](client.md#paho.mqtt.client.Client.on_connect_fail), [`on_disconnect`](client.md#paho.mqtt.client.Client.on_disconnect), [`on_message`](client.md#paho.mqtt.client.Client.on_message), [`on_publish`](client.md#paho.mqtt.client.Client.on_publish),
[`on_subscribe`](client.md#paho.mqtt.client.Client.on_subscribe), [`on_unsubscribe`](client.md#paho.mqtt.client.Client.on_unsubscribe), [`on_log`](client.md#paho.mqtt.client.Client.on_log), [`on_socket_open`](client.md#paho.mqtt.client.Client.on_socket_open), [`on_socket_close`](client.md#paho.mqtt.client.Client.on_socket_close),
[`on_socket_register_write`](client.md#paho.mqtt.client.Client.on_socket_register_write), [`on_socket_unregister_write`](client.md#paho.mqtt.client.Client.on_socket_unregister_write)

#### VERSION1 *= 1*

The version used with paho-mqtt 1.x before introducing CallbackAPIVersion.

This version had different arguments depending if MQTTv5 or MQTTv3 was used. [`Properties`](#paho.mqtt.properties.Properties) & [`ReasonCode`](#paho.mqtt.reasoncodes.ReasonCode) were missing
on some callback (apply only to MQTTv5).

This version is deprecated and will be removed in version 3.0.

#### VERSION2 *= 2*

This version fix some of the shortcoming of previous version.

Callback have the same signature if using MQTTv5 or MQTTv3. [`ReasonCode`](#paho.mqtt.reasoncodes.ReasonCode) are used in MQTTv3.

### *class* paho.mqtt.enums.ConnackCode(value, names=None, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

#### CONNACK_ACCEPTED *= 0*

#### CONNACK_REFUSED_BAD_USERNAME_PASSWORD *= 4*

#### CONNACK_REFUSED_IDENTIFIER_REJECTED *= 2*

#### CONNACK_REFUSED_NOT_AUTHORIZED *= 5*

#### CONNACK_REFUSED_PROTOCOL_VERSION *= 1*

#### CONNACK_REFUSED_SERVER_UNAVAILABLE *= 3*

### *class* paho.mqtt.enums.LogLevel(value, names=None, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

#### MQTT_LOG_DEBUG *= 16*

#### MQTT_LOG_ERR *= 8*

#### MQTT_LOG_INFO *= 1*

#### MQTT_LOG_NOTICE *= 2*

#### MQTT_LOG_WARNING *= 4*

### *class* paho.mqtt.enums.MQTTErrorCode(value, names=None, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

#### MQTT_ERR_ACL_DENIED *= 12*

#### MQTT_ERR_AGAIN *= -1*

#### MQTT_ERR_AUTH *= 11*

#### MQTT_ERR_CONN_LOST *= 7*

#### MQTT_ERR_CONN_REFUSED *= 5*

#### MQTT_ERR_ERRNO *= 14*

#### MQTT_ERR_INVAL *= 3*

#### MQTT_ERR_KEEPALIVE *= 16*

#### MQTT_ERR_NOMEM *= 1*

#### MQTT_ERR_NOT_FOUND *= 6*

#### MQTT_ERR_NOT_SUPPORTED *= 10*

#### MQTT_ERR_NO_CONN *= 4*

#### MQTT_ERR_PAYLOAD_SIZE *= 9*

#### MQTT_ERR_PROTOCOL *= 2*

#### MQTT_ERR_QUEUE_SIZE *= 15*

#### MQTT_ERR_SUCCESS *= 0*

#### MQTT_ERR_TLS *= 8*

#### MQTT_ERR_UNKNOWN *= 13*

### *class* paho.mqtt.enums.MQTTProtocolVersion(value, names=None, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

#### MQTTv31 *= 3*

#### MQTTv311 *= 4*

#### MQTTv5 *= 5*

### *class* paho.mqtt.enums.MessageState(value, names=None, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

#### MQTT_MS_INVALID *= 0*

#### MQTT_MS_PUBLISH *= 1*

#### MQTT_MS_QUEUED *= 9*

#### MQTT_MS_RESEND_PUBCOMP *= 6*

#### MQTT_MS_RESEND_PUBREL *= 4*

#### MQTT_MS_SEND_PUBREC *= 8*

#### MQTT_MS_WAIT_FOR_PUBACK *= 2*

#### MQTT_MS_WAIT_FOR_PUBCOMP *= 7*

#### MQTT_MS_WAIT_FOR_PUBREC *= 3*

#### MQTT_MS_WAIT_FOR_PUBREL *= 5*

### *class* paho.mqtt.enums.MessageType(value, names=None, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

#### AUTH *= 240*

#### CONNACK *= 32*

#### CONNECT *= 16*

#### DISCONNECT *= 224*

#### PINGREQ *= 192*

#### PINGRESP *= 208*

#### PUBACK *= 64*

#### PUBCOMP *= 112*

#### PUBLISH *= 48*

#### PUBREC *= 80*

#### PUBREL *= 96*

#### SUBACK *= 144*

#### SUBSCRIBE *= 128*

#### UNSUBACK *= 176*

#### UNSUBSCRIBE *= 160*

### *class* paho.mqtt.enums.PahoClientMode(value, names=None, \*values, module=None, qualname=None, type=None, start=1, boundary=None)

#### MQTT_BRIDGE *= 1*

#### MQTT_CLIENT *= 0*

<a id="module-paho.mqtt.properties"></a>

### *exception* paho.mqtt.properties.MQTTException

### *exception* paho.mqtt.properties.MalformedPacket

### *class* paho.mqtt.properties.Properties(packetType)

MQTT v5.0 properties class.

See Properties.names for a list of accepted property names along with their numeric values.

See Properties.properties for the data type of each property.

Example of use:

```default
publish_properties = Properties(PacketTypes.PUBLISH)
publish_properties.UserProperty = ("a", "2")
publish_properties.UserProperty = ("c", "3")
```

First the object is created with packet type as argument, no properties will be present at
this point. Then properties are added as attributes, the name of which is the string property
name without the spaces.

#### allowsMultiple(compressedName)

#### clear()

#### getIdentFromName(compressedName)

#### getNameFromIdent(identifier)

#### isEmpty()

#### json()

#### pack()

#### readProperty(buffer, type, propslen)

#### unpack(buffer)

#### writeProperty(identifier, type, value)

### *class* paho.mqtt.properties.VariableByteIntegers

MQTT variable byte integer helper class.  Used
in several places in MQTT v5.0 properties.

#### *static* decode(buffer)

Get the value of a multi-byte integer from a buffer
Return the value, and the number of bytes used.

[MQTT-1.5.5-1] the encoded value MUST use the minimum number of bytes necessary to represent the value

#### *static* encode(x)

Convert an integer 0 <= x <= 268435455 into multi-byte format.
Returns the buffer converted from the integer.

### paho.mqtt.properties.readBytes(buffer)

### paho.mqtt.properties.readInt16(buf)

### paho.mqtt.properties.readInt32(buf)

### paho.mqtt.properties.readUTF(buffer, maxlen)

### paho.mqtt.properties.writeBytes(buffer)

### paho.mqtt.properties.writeInt16(length)

### paho.mqtt.properties.writeInt32(length)

### paho.mqtt.properties.writeUTF(data)

<a id="module-paho.mqtt.reasoncodes"></a>

### *class* paho.mqtt.reasoncodes.ReasonCode(packetType, aName='Success', identifier=-1)

MQTT version 5.0 reason codes class.

See ReasonCode.names for a list of possible numeric values along with their
names and the packets to which they apply.

#### getId(name)

Get the numeric id corresponding to a reason code name.

Used when setting the reason code for a packetType
check that only valid codes for the packet are set.

#### getName()

Returns the reason code name corresponding to the numeric value which is set.

#### *property* is_failure *: bool*

#### json()

#### pack()

#### set(name)

#### unpack(buffer)

### *class* paho.mqtt.reasoncodes.ReasonCodes(\*args, \*\*kwargs)
