# client module

<!-- exclude-members exclude decorator for callback, because decorator are
documented in there respective on_XXX -->

<a id="module-paho.mqtt.client"></a>

This is an MQTT client module. MQTT is a lightweight pub/sub messaging
protocol that is easy to implement and suitable for low powered devices.

### *class* paho.mqtt.client.Client(callback_api_version: [CallbackAPIVersion](types.md#paho.mqtt.enums.CallbackAPIVersion), client_id: str = '', clean_session: bool | None = None, userdata: Any = None, protocol: int = MQTTProtocolVersion.MQTTv311, transport: Literal['tcp', 'websockets'] = 'tcp', reconnect_on_failure: bool = True, manual_ack: bool = False)

MQTT version 3.1/3.1.1/5.0 client class.

This is the main class for use communicating with an MQTT broker.

General usage flow:

* Use [`connect()`](#paho.mqtt.client.Client.connect), [`connect_async()`](#paho.mqtt.client.Client.connect_async) or [`connect_srv()`](#paho.mqtt.client.Client.connect_srv) to connect to a broker
* Use [`loop_start()`](#paho.mqtt.client.Client.loop_start) to set a thread running to call [`loop()`](#paho.mqtt.client.Client.loop) for you.
* Or use [`loop_forever()`](#paho.mqtt.client.Client.loop_forever) to handle calling [`loop()`](#paho.mqtt.client.Client.loop) for you in a blocking function.
* Or call [`loop()`](#paho.mqtt.client.Client.loop) frequently to maintain network traffic flow with the broker
* Use [`subscribe()`](#paho.mqtt.client.Client.subscribe) to subscribe to a topic and receive messages
* Use [`publish()`](#paho.mqtt.client.Client.publish) to send messages
* Use [`disconnect()`](#paho.mqtt.client.Client.disconnect) to disconnect from the broker

Data returned from the broker is made available with the use of callback
functions as described below.

* **Parameters:**
  * **callback_api_version** ([*CallbackAPIVersion*](types.md#paho.mqtt.enums.CallbackAPIVersion)) – define the API version for user-callback (on_connect, on_publish,…).
    This field is required and it’s recommended to use the latest version (CallbackAPIVersion.API_VERSION2).
    See each callback for description of API for each version. The file migrations.md contains details on
    how to migrate between version.
  * **client_id** (*str*) – the unique client id string used when connecting to the
    broker. If client_id is zero length or None, then the behaviour is
    defined by which protocol version is in use. If using MQTT v3.1.1, then
    a zero length client id will be sent to the broker and the broker will
    generate a random for the client. If using MQTT v3.1 then an id will be
    randomly generated. In both cases, clean_session must be True. If this
    is not the case a ValueError will be raised.
  * **clean_session** (*bool*) – a boolean that determines the client type. If True,
    the broker will remove all information about this client when it
    disconnects. If False, the client is a persistent client and
    subscription information and queued messages will be retained when the
    client disconnects.
    Note that a client will never discard its own outgoing messages on
    disconnect. Calling connect() or reconnect() will cause the messages to
    be resent.  Use reinitialise() to reset a client to its original state.
    The clean_session argument only applies to MQTT versions v3.1.1 and v3.1.
    It is not accepted if the MQTT version is v5.0 - use the clean_start
    argument on connect() instead.
  * **userdata** – user defined data of any type that is passed as the “userdata”
    parameter to callbacks. It may be updated at a later point with the
    user_data_set() function.
  * **protocol** (*int*) – allows explicit setting of the MQTT version to
    use for this client. Can be paho.mqtt.client.MQTTv311 (v3.1.1),
    paho.mqtt.client.MQTTv31 (v3.1) or paho.mqtt.client.MQTTv5 (v5.0),
    with the default being v3.1.1.
  * **transport** – use “websockets” to use WebSockets as the transport
    mechanism. Set to “tcp” to use raw TCP, which is the default.
  * **manual_ack** (*bool*) – normally, when a message is received, the library automatically
    acknowledges after on_message callback returns.  manual_ack=True allows the application to
    acknowledge receipt after it has completed processing of a message
    using a the ack() method. This addresses vulnerability to message loss
    if applications fails while processing a message, or while it pending
    locally.

## Callbacks

A number of callback functions are available to receive data back from the
broker. To use a callback, define a function and then assign it to the
client:

```default
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")

client.on_connect = on_connect
```

Callbacks can also be attached using decorators:

```default
mqttc = paho.mqtt.Client()

@mqttc.connect_callback()
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
```

All of the callbacks as described below have a “client” and an “userdata”
argument. “client” is the [`Client`](#paho.mqtt.client.Client) instance that is calling the callback.
userdata” is user data of any type and can be set when creating a new client
instance or with [`user_data_set()`](#paho.mqtt.client.Client.user_data_set).

If you wish to suppress exceptions within a callback, you should set
`mqttc.suppress_exceptions = True`

The callbacks are listed below, documentation for each of them can be found
at the same function name:

[`on_connect`](#paho.mqtt.client.Client.on_connect), [`on_connect_fail`](#paho.mqtt.client.Client.on_connect_fail), [`on_disconnect`](#paho.mqtt.client.Client.on_disconnect), [`on_message`](#paho.mqtt.client.Client.on_message), [`on_publish`](#paho.mqtt.client.Client.on_publish),
[`on_subscribe`](#paho.mqtt.client.Client.on_subscribe), [`on_unsubscribe`](#paho.mqtt.client.Client.on_unsubscribe), [`on_log`](#paho.mqtt.client.Client.on_log), [`on_socket_open`](#paho.mqtt.client.Client.on_socket_open), [`on_socket_close`](#paho.mqtt.client.Client.on_socket_close),
[`on_socket_register_write`](#paho.mqtt.client.Client.on_socket_register_write), [`on_socket_unregister_write`](#paho.mqtt.client.Client.on_socket_unregister_write)

#### ack(mid: int, qos: int)

send an acknowledgement for a given message id (stored in [`message.mid`](#paho.mqtt.client.MQTTMessage.mid)).
only useful in QoS>=1 and `manual_ack=True` (option of [`Client`](#paho.mqtt.client.Client))

#### *property* callback_api_version *: [CallbackAPIVersion](types.md#paho.mqtt.enums.CallbackAPIVersion)*

Return the callback API version used for user-callback. See docstring for
each user-callback ([`on_connect`](#paho.mqtt.client.Client.on_connect), [`on_publish`](#paho.mqtt.client.Client.on_publish), …) for details.

This property is read-only.

#### connect(host: str, port: int = 1883, keepalive: int = 60, bind_address: str = '', bind_port: int = 0, clean_start: bool | Literal[3] = 3, properties: [Properties](types.md#paho.mqtt.properties.Properties) | None = None)

Connect to a remote broker. This is a blocking call that establishes
the underlying connection and transmits a CONNECT packet.
Note that the connection status will not be updated until a CONNACK is received and
processed (this requires a running network loop, see [`loop_start`](#paho.mqtt.client.Client.loop_start), [`loop_forever`](#paho.mqtt.client.Client.loop_forever), [`loop`](#paho.mqtt.client.Client.loop)…).

* **Parameters:**
  * **host** (*str*) – the hostname or IP address of the remote broker.
  * **port** (*int*) – the network port of the server host to connect to. Defaults to
    1883. Note that the default port for MQTT over SSL/TLS is 8883 so if you
    are using [`tls_set()`](#paho.mqtt.client.Client.tls_set) the port may need providing.
  * **keepalive** (*int*) – Maximum period in seconds between communications with the
    broker. If no other messages are being exchanged, this controls the
    rate at which the client will send ping messages to the broker.
  * **clean_start** (*bool*) – (MQTT v5.0 only) True, False or MQTT_CLEAN_START_FIRST_ONLY.
    Sets the MQTT v5.0 clean_start flag always, never or on the first successful connect only,
    respectively.  MQTT session data (such as outstanding messages and subscriptions)
    is cleared on successful connect when the clean_start flag is set.
    For MQTT v3.1.1, the `clean_session` argument of [`Client`](#paho.mqtt.client.Client) should be used for similar
    result.
  * **properties** ([*Properties*](types.md#paho.mqtt.properties.Properties)) – (MQTT v5.0 only) the MQTT v5.0 properties to be sent in the
    MQTT connect packet.

#### connect_async(host: str, port: int = 1883, keepalive: int = 60, bind_address: str = '', bind_port: int = 0, clean_start: bool | Literal[3] = 3, properties: [Properties](types.md#paho.mqtt.properties.Properties) | None = None)

Connect to a remote broker asynchronously. This is a non-blocking
connect call that can be used with [`loop_start()`](#paho.mqtt.client.Client.loop_start) to provide very quick
start.

Any already established connection will be terminated immediately.

* **Parameters:**
  * **host** (*str*) – the hostname or IP address of the remote broker.
  * **port** (*int*) – the network port of the server host to connect to. Defaults to
    1883. Note that the default port for MQTT over SSL/TLS is 8883 so if you
    are using [`tls_set()`](#paho.mqtt.client.Client.tls_set) the port may need providing.
  * **keepalive** (*int*) – Maximum period in seconds between communications with the
    broker. If no other messages are being exchanged, this controls the
    rate at which the client will send ping messages to the broker.
  * **clean_start** (*bool*) – (MQTT v5.0 only) True, False or MQTT_CLEAN_START_FIRST_ONLY.
    Sets the MQTT v5.0 clean_start flag always, never or on the first successful connect only,
    respectively.  MQTT session data (such as outstanding messages and subscriptions)
    is cleared on successful connect when the clean_start flag is set.
    For MQTT v3.1.1, the `clean_session` argument of [`Client`](#paho.mqtt.client.Client) should be used for similar
    result.
  * **properties** ([*Properties*](types.md#paho.mqtt.properties.Properties)) – (MQTT v5.0 only) the MQTT v5.0 properties to be sent in the
    MQTT connect packet.

#### connect_srv(domain: str | None = None, keepalive: int = 60, bind_address: str = '', bind_port: int = 0, clean_start: bool | Literal[3] = 3, properties: [Properties](types.md#paho.mqtt.properties.Properties) | None = None)

Connect to a remote broker.

* **Parameters:**
  * **domain** (*str*) – the DNS domain to search for SRV records; if None,
    try to determine local domain name.
  * **properties** (*keepalive* *,* *bind_address* *,* *clean_start and*) – see [`connect()`](#paho.mqtt.client.Client.connect)

#### *property* connect_timeout *: float*

Connection establishment timeout in seconds.

This property may not be changed if the connection is already open.

#### disable_logger()

Disable logging using standard python logging package. This has no effect on the [`on_log`](#paho.mqtt.client.Client.on_log) callback.

#### disconnect(reasoncode: [ReasonCode](types.md#paho.mqtt.reasoncodes.ReasonCode) | None = None, properties: [Properties](types.md#paho.mqtt.properties.Properties) | None = None)

Disconnect a connected client from the broker.

* **Parameters:**
  * **reasoncode** ([*ReasonCode*](types.md#paho.mqtt.reasoncodes.ReasonCode)) – (MQTT v5.0 only) a ReasonCode instance setting the MQTT v5.0
    reasoncode to be sent with the disconnect packet. It is optional, the receiver
    then assuming that 0 (success) is the value.
  * **properties** ([*Properties*](types.md#paho.mqtt.properties.Properties)) – (MQTT v5.0 only) a Properties instance setting the MQTT v5.0 properties
    to be included. Optional - if not set, no properties are sent.

#### enable_bridge_mode()

Sets the client in a bridge mode instead of client mode.

Must be called before [`connect()`](#paho.mqtt.client.Client.connect) to have any effect.
Requires brokers that support bridge mode.

Under bridge mode, the broker will identify the client as a bridge and
not send it’s own messages back to it. Hence a subsciption of # is
possible without message loops. This feature also correctly propagates
the retain flag on the messages.

Currently Mosquitto and RSMB support this feature. This feature can
be used to create a bridge between multiple broker.

#### enable_logger(logger: Logger | None = None)

Enables a logger to send log messages to

* **Parameters:**
  **logger** (*logging.Logger*) – if specified, that `logging.Logger` object will be used, otherwise
  one will be created automatically.

See [`disable_logger`](#paho.mqtt.client.Client.disable_logger) to undo this action.

#### *property* host *: str*

Host to connect to. If [`connect()`](#paho.mqtt.client.Client.connect) hasn’t been called yet, returns an empty string.

This property may not be changed if the connection is already open.

#### is_connected()

Returns the current status of the connection

True if connection exists
False if connection is closed

#### *property* keepalive *: int*

Client keepalive interval (in seconds).

This property may not be changed if the connection is already open.

#### *property* logger *: Logger | None*

#### loop(timeout: float = 1.0)

Process network events.

It is strongly recommended that you use [`loop_start()`](#paho.mqtt.client.Client.loop_start), or
[`loop_forever()`](#paho.mqtt.client.Client.loop_forever), or if you are using an external event loop using
[`loop_read()`](#paho.mqtt.client.Client.loop_read), [`loop_write()`](#paho.mqtt.client.Client.loop_write), and [`loop_misc()`](#paho.mqtt.client.Client.loop_misc). Using loop() on it’s own is
no longer recommended.

This function must be called regularly to ensure communication with the
broker is carried out. It calls select() on the network socket to wait
for network events. If incoming data is present it will then be
processed. Outgoing commands, from e.g. [`publish()`](#paho.mqtt.client.Client.publish), are normally sent
immediately that their function is called, but this is not always
possible. loop() will also attempt to send any remaining outgoing
messages, which also includes commands that are part of the flow for
messages with QoS>0.

* **Parameters:**
  **timeout** (*int*) – The time in seconds to wait for incoming/outgoing network
  traffic before timing out and returning.

Returns MQTT_ERR_SUCCESS on success.
Returns >0 on error.

A ValueError will be raised if timeout < 0

#### loop_forever(timeout: float = 1.0, retry_first_connection: bool = False)

This function calls the network loop functions for you in an
infinite blocking loop. It is useful for the case where you only want
to run the MQTT client loop in your program.

loop_forever() will handle reconnecting for you if reconnect_on_failure is
true (this is the default behavior). If you call [`disconnect()`](#paho.mqtt.client.Client.disconnect) in a callback
it will return.

* **Parameters:**
  * **timeout** (*int*) – The time in seconds to wait for incoming/outgoing network
    traffic before timing out and returning.
  * **retry_first_connection** (*bool*) – Should the first connection attempt be retried on failure.
    This is independent of the reconnect_on_failure setting.
* **Raises:**
  **OSError** – if the first connection fail unless retry_first_connection=True

#### loop_misc()

Process miscellaneous network events. Use in place of calling [`loop()`](#paho.mqtt.client.Client.loop) if you
wish to call select() or equivalent on.

Do not use if you are using [`loop_start()`](#paho.mqtt.client.Client.loop_start) or [`loop_forever()`](#paho.mqtt.client.Client.loop_forever).

#### loop_read(max_packets: int = 1)

Process read network events. Use in place of calling [`loop()`](#paho.mqtt.client.Client.loop) if you
wish to handle your client reads as part of your own application.

Use [`socket()`](#paho.mqtt.client.Client.socket) to obtain the client socket to call select() or equivalent
on.

Do not use if you are using [`loop_start()`](#paho.mqtt.client.Client.loop_start) or [`loop_forever()`](#paho.mqtt.client.Client.loop_forever).

#### loop_start()

This is part of the threaded client interface. Call this once to
start a new thread to process network traffic. This provides an
alternative to repeatedly calling [`loop()`](#paho.mqtt.client.Client.loop) yourself.

Under the hood, this will call [`loop_forever`](#paho.mqtt.client.Client.loop_forever) in a thread, which means that
the thread will terminate if you call [`disconnect()`](#paho.mqtt.client.Client.disconnect)

#### loop_stop()

This is part of the threaded client interface. Call this once to
stop the network thread previously created with [`loop_start()`](#paho.mqtt.client.Client.loop_start). This call
will block until the network thread finishes.

This don’t guarantee that publish packet are sent, use [`wait_for_publish`](#paho.mqtt.client.MQTTMessageInfo.wait_for_publish) or
[`on_publish`](#paho.mqtt.client.Client.on_publish) to ensure [`publish`](#paho.mqtt.client.Client.publish) are sent.

#### loop_write()

Process write network events. Use in place of calling [`loop()`](#paho.mqtt.client.Client.loop) if you
wish to handle your client writes as part of your own application.

Use [`socket()`](#paho.mqtt.client.Client.socket) to obtain the client socket to call select() or equivalent
on.

Use [`want_write()`](#paho.mqtt.client.Client.want_write) to determine if there is data waiting to be written.

Do not use if you are using [`loop_start()`](#paho.mqtt.client.Client.loop_start) or [`loop_forever()`](#paho.mqtt.client.Client.loop_forever).

#### manual_ack_set(on: bool)

The paho library normally acknowledges messages as soon as they are delivered to the caller.
If manual_ack is turned on, then the caller MUST manually acknowledge every message once
application processing is complete using [`ack()`](#paho.mqtt.client.Client.ack)

#### *property* max_inflight_messages *: int*

Maximum number of messages with QoS > 0 that can be partway through the network flow at once

This property may not be changed if the connection is already open.

#### max_inflight_messages_set(inflight: int)

Set the maximum number of messages with QoS>0 that can be part way
through their network flow at once. Defaults to 20.

#### *property* max_queued_messages *: int*

Maximum number of message in the outgoing message queue, 0 means unlimited

This property may not be changed if the connection is already open.

#### max_queued_messages_set(queue_size: int)

Set the maximum number of messages in the outgoing message queue.
0 means unlimited.

#### message_callback_add(sub: str, callback: Callable[[[Client](#paho.mqtt.client.Client), Any, [MQTTMessage](#paho.mqtt.client.MQTTMessage)], None])

Register a message callback for a specific topic.
Messages that match ‘sub’ will be passed to ‘callback’. Any
non-matching messages will be passed to the default [`on_message`](#paho.mqtt.client.Client.on_message)
callback.

Call multiple times with different ‘sub’ to define multiple topic
specific callbacks.

Topic specific callbacks may be removed with
[`message_callback_remove()`](#paho.mqtt.client.Client.message_callback_remove).

See [`on_message`](#paho.mqtt.client.Client.on_message) for the expected signature of the callback.

Decorator: @client.topic_callback(sub) (`client` is the name of the
: instance which this callback is being attached to)

Example:

```default
@client.topic_callback("mytopic/#")
def handle_mytopic(client, userdata, message):
    ...
```

#### message_callback_remove(sub: str)

Remove a message callback previously registered with
[`message_callback_add()`](#paho.mqtt.client.Client.message_callback_add).

#### *property* on_connect *: Callable[[[Client](#paho.mqtt.client.Client), Any, Dict[str, Any], [ReasonCode](types.md#paho.mqtt.reasoncodes.ReasonCode), [Properties](types.md#paho.mqtt.properties.Properties) | None], None] | Callable[[[Client](#paho.mqtt.client.Client), Any, Dict[str, Any], [MQTTErrorCode](types.md#paho.mqtt.enums.MQTTErrorCode)], None] | Callable[[[Client](#paho.mqtt.client.Client), Any, [ConnectFlags](#paho.mqtt.client.ConnectFlags), [ReasonCode](types.md#paho.mqtt.reasoncodes.ReasonCode), [Properties](types.md#paho.mqtt.properties.Properties) | None], None] | None*

The callback called when the broker reponds to our connection request.

Expected signature for callback API version 2:

```default
connect_callback(client, userdata, connect_flags, reason_code, properties)
```

Expected signature for callback API version 1 change with MQTT protocol version:
: * For MQTT v3.1 and v3.1.1 it’s:
    ```default
    connect_callback(client, userdata, flags, rc)
    ```
  * For MQTT it’s v5.0:
    ```default
    connect_callback(client, userdata, flags, reason_code, properties)
    ```

* **Parameters:**
  * **client** ([*Client*](#paho.mqtt.client.Client)) – the client instance for this callback
  * **userdata** – the private user data as set in Client() or user_data_set()
  * **connect_flags** ([*ConnectFlags*](#paho.mqtt.client.ConnectFlags)) – the flags for this connection
  * **reason_code** ([*ReasonCode*](types.md#paho.mqtt.reasoncodes.ReasonCode)) – the connection reason code received from the broken.
    In MQTT v5.0 it’s the reason code defined by the standard.
    In MQTT v3, we convert return code to a reason code, see
    [`convert_connack_rc_to_reason_code()`](#paho.mqtt.client.convert_connack_rc_to_reason_code).
    [`ReasonCode`](types.md#paho.mqtt.reasoncodes.ReasonCode) may be compared to integer.
  * **properties** ([*Properties*](types.md#paho.mqtt.properties.Properties)) – the MQTT v5.0 properties received from the broker.
    For MQTT v3.1 and v3.1.1 properties is not provided and an empty Properties
    object is always used.
  * **flags** (*dict*) – response flags sent by the broker
  * **rc** (*int*) – the connection result, should have a value of [`ConnackCode`](types.md#paho.mqtt.enums.ConnackCode)

flags is a dict that contains response flags from the broker:
: flags[‘session present’] - this flag is useful for clients that are
  : using clean session set to 0 only. If a client with clean
    session=0, that reconnects to a broker that it has previously
    connected to, this flag indicates whether the broker still has the
    session information for the client. If 1, the session still exists.

The value of rc indicates success or not:
: - 0: Connection successful
  - 1: Connection refused - incorrect protocol version
  - 2: Connection refused - invalid client identifier
  - 3: Connection refused - server unavailable
  - 4: Connection refused - bad username or password
  - 5: Connection refused - not authorised
  - 6-255: Currently unused.

Decorator: @client.connect_callback() (`client` is the name of the
: instance which this callback is being attached to)

#### *property* on_connect_fail *: Callable[[[Client](#paho.mqtt.client.Client), Any], None] | None*

The callback called when the client failed to connect
to the broker.

Expected signature is (for all callback_api_version):

```default
connect_fail_callback(client, userdata)
```

* **Parameters:**
  **client** ([*Client*](#paho.mqtt.client.Client)) – the client instance for this callback
* **Parama userdata:**
  the private user data as set in Client() or user_data_set()

Decorator: @client.connect_fail_callback() (`client` is the name of the
: instance which this callback is being attached to)

#### *property* on_disconnect *: Callable[[[Client](#paho.mqtt.client.Client), Any, [MQTTErrorCode](types.md#paho.mqtt.enums.MQTTErrorCode)], None] | Callable[[[Client](#paho.mqtt.client.Client), Any, [ReasonCode](types.md#paho.mqtt.reasoncodes.ReasonCode) | int | None, [Properties](types.md#paho.mqtt.properties.Properties) | None], None] | Callable[[[Client](#paho.mqtt.client.Client), Any, [DisconnectFlags](#paho.mqtt.client.DisconnectFlags), [ReasonCode](types.md#paho.mqtt.reasoncodes.ReasonCode), [Properties](types.md#paho.mqtt.properties.Properties) | None], None] | None*

The callback called when the client disconnects from the broker.

Expected signature for callback API version 2:

```default
disconnect_callback(client, userdata, disconnect_flags, reason_code, properties)
```

Expected signature for callback API version 1 change with MQTT protocol version:
: * For MQTT v3.1 and v3.1.1 it’s:
    ```default
    disconnect_callback(client, userdata, rc)
    ```
  * For MQTT it’s v5.0:
    ```default
    disconnect_callback(client, userdata, reason_code, properties)
    ```

* **Parameters:**
  * **client** ([*Client*](#paho.mqtt.client.Client)) – the client instance for this callback
  * **userdata** – the private user data as set in Client() or user_data_set()
  * **disconnect_flags** (*DisconnectFlag*) – the flags for this disconnection.
  * **reason_code** ([*ReasonCode*](types.md#paho.mqtt.reasoncodes.ReasonCode)) – the disconnection reason code possibly received from the broker (see disconnect_flags).
    In MQTT v5.0 it’s the reason code defined by the standard.
    In MQTT v3 it’s never received from the broker, we convert an MQTTErrorCode,
    see [`convert_disconnect_error_code_to_reason_code()`](#paho.mqtt.client.convert_disconnect_error_code_to_reason_code).
    [`ReasonCode`](types.md#paho.mqtt.reasoncodes.ReasonCode) may be compared to integer.
  * **properties** ([*Properties*](types.md#paho.mqtt.properties.Properties)) – the MQTT v5.0 properties received from the broker.
    For MQTT v3.1 and v3.1.1 properties is not provided and an empty Properties
    object is always used.
  * **rc** (*int*) – the disconnection result
    The rc parameter indicates the disconnection state. If
    MQTT_ERR_SUCCESS (0), the callback was called in response to
    a disconnect() call. If any other value the disconnection
    was unexpected, such as might be caused by a network error.

Decorator: @client.disconnect_callback() (`client` is the name of the
: instance which this callback is being attached to)

#### *property* on_log *: Callable[[[Client](#paho.mqtt.client.Client), Any, int, str], None] | None*

The callback called when the client has log information.
Defined to allow debugging.

Expected signature is:

```default
log_callback(client, userdata, level, buf)
```

* **Parameters:**
  * **client** ([*Client*](#paho.mqtt.client.Client)) – the client instance for this callback
  * **userdata** – the private user data as set in Client() or user_data_set()
  * **level** (*int*) – gives the severity of the message and will be one of
    MQTT_LOG_INFO, MQTT_LOG_NOTICE, MQTT_LOG_WARNING,
    MQTT_LOG_ERR, and MQTT_LOG_DEBUG.
  * **buf** (*str*) – the message itself

Decorator: @client.log_callback() (`client` is the name of the
: instance which this callback is being attached to)

#### *property* on_message *: Callable[[[Client](#paho.mqtt.client.Client), Any, [MQTTMessage](#paho.mqtt.client.MQTTMessage)], None] | None*

The callback called when a message has been received on a topic
that the client subscribes to.

This callback will be called for every message received unless a
[`message_callback_add()`](#paho.mqtt.client.Client.message_callback_add) matched the message.

Expected signature is (for all callback API version):
: message_callback(client, userdata, message)

* **Parameters:**
  * **client** ([*Client*](#paho.mqtt.client.Client)) – the client instance for this callback
  * **userdata** – the private user data as set in Client() or user_data_set()
  * **message** ([*MQTTMessage*](#paho.mqtt.client.MQTTMessage)) – the received message.
    This is a class with members topic, payload, qos, retain.

Decorator: @client.message_callback() (`client` is the name of the
: instance which this callback is being attached to)

#### *property* on_pre_connect *: Callable[[[Client](#paho.mqtt.client.Client), Any], None] | None*

The callback called immediately prior to the connection is made
request.

Expected signature (for all callback API version):

```default
connect_callback(client, userdata)
```

* **Parama Client client:**
  the client instance for this callback
* **Parama userdata:**
  the private user data as set in Client() or user_data_set()

Decorator: @client.pre_connect_callback() (`client` is the name of the
: instance which this callback is being attached to)

#### *property* on_publish *: Callable[[[Client](#paho.mqtt.client.Client), Any, int], None] | Callable[[[Client](#paho.mqtt.client.Client), Any, int, [ReasonCode](types.md#paho.mqtt.reasoncodes.ReasonCode), [Properties](types.md#paho.mqtt.properties.Properties)], None] | None*

The callback called when a message that was to be sent using the
[`publish()`](#paho.mqtt.client.Client.publish) call has completed transmission to the broker.

For messages with QoS levels 1 and 2, this means that the appropriate
handshakes have completed. For QoS 0, this simply means that the message
has left the client.
This callback is important because even if the [`publish()`](#paho.mqtt.client.Client.publish) call returns
success, it does not always mean that the message has been sent.

See also [`wait_for_publish`](#paho.mqtt.client.MQTTMessageInfo.wait_for_publish) which could be simpler to use.

Expected signature for callback API version 2:

```default
publish_callback(client, userdata, mid, reason_code, properties)
```

Expected signature for callback API version 1:

```default
publish_callback(client, userdata, mid)
```

* **Parameters:**
  * **client** ([*Client*](#paho.mqtt.client.Client)) – the client instance for this callback
  * **userdata** – the private user data as set in Client() or user_data_set()
  * **mid** (*int*) – matches the mid variable returned from the corresponding
    [`publish()`](#paho.mqtt.client.Client.publish) call, to allow outgoing messages to be tracked.
  * **reason_code** ([*ReasonCode*](types.md#paho.mqtt.reasoncodes.ReasonCode)) – the connection reason code received from the broken.
    In MQTT v5.0 it’s the reason code defined by the standard.
    In MQTT v3 it’s always the reason code Success
* **Parama Properties properties:**
  the MQTT v5.0 properties received from the broker.
  For MQTT v3.1 and v3.1.1 properties is not provided and an empty Properties
  object is always used.

Note: for QoS = 0, the reason_code and the properties don’t really exist, it’s the client
library that generate them. It’s always an empty properties and a success reason code.
Because the (MQTTv5) standard don’t have reason code for PUBLISH packet, the library create them
at PUBACK packet, as if the message was sent with QoS = 1.

Decorator: @client.publish_callback() (`client` is the name of the
: instance which this callback is being attached to)

#### *property* on_socket_close *: CallbackOnSocket | None*

The callback called just before the socket is closed.

This should be used to unregister the socket from an external event loop for reading.

Expected signature is (for all callback API version):

```default
socket_close_callback(client, userdata, socket)
```

* **Parameters:**
  * **client** ([*Client*](#paho.mqtt.client.Client)) – the client instance for this callback
  * **userdata** – the private user data as set in Client() or user_data_set()
  * **sock** (*SocketLike*) – the socket which is about to be closed.

Decorator: @client.socket_close_callback() (`client` is the name of the
: instance which this callback is being attached to)

#### *property* on_socket_open *: CallbackOnSocket | None*

The callback called just after the socket was opend.

This should be used to register the socket to an external event loop for reading.

Expected signature is (for all callback API version):

```default
socket_open_callback(client, userdata, socket)
```

* **Parameters:**
  * **client** ([*Client*](#paho.mqtt.client.Client)) – the client instance for this callback
  * **userdata** – the private user data as set in Client() or user_data_set()
  * **sock** (*SocketLike*) – the socket which was just opened.

Decorator: @client.socket_open_callback() (`client` is the name of the
: instance which this callback is being attached to)

#### *property* on_socket_register_write *: CallbackOnSocket | None*

The callback called when the socket needs writing but can’t.

This should be used to register the socket with an external event loop for writing.

Expected signature is (for all callback API version):

```default
socket_register_write_callback(client, userdata, socket)
```

* **Parameters:**
  * **client** ([*Client*](#paho.mqtt.client.Client)) – the client instance for this callback
  * **userdata** – the private user data as set in Client() or user_data_set()
  * **sock** (*SocketLike*) – the socket which should be registered for writing

Decorator: @client.socket_register_write_callback() (`client` is the name of the
: instance which this callback is being attached to)

#### *property* on_socket_unregister_write *: CallbackOnSocket | None*

The callback called when the socket doesn’t need writing anymore.

This should be used to unregister the socket from an external event loop for writing.

Expected signature is (for all callback API version):

```default
socket_unregister_write_callback(client, userdata, socket)
```

* **Parameters:**
  * **client** ([*Client*](#paho.mqtt.client.Client)) – the client instance for this callback
  * **userdata** – the private user data as set in Client() or user_data_set()
  * **sock** (*SocketLike*) – the socket which should be unregistered for writing

Decorator: @client.socket_unregister_write_callback() (`client` is the name of the
: instance which this callback is being attached to)

#### *property* on_subscribe *: Callable[[[Client](#paho.mqtt.client.Client), Any, int, Tuple[int, ...]], None] | Callable[[[Client](#paho.mqtt.client.Client), Any, int, List[[ReasonCode](types.md#paho.mqtt.reasoncodes.ReasonCode)], [Properties](types.md#paho.mqtt.properties.Properties)], None] | Callable[[[Client](#paho.mqtt.client.Client), Any, int, List[[ReasonCode](types.md#paho.mqtt.reasoncodes.ReasonCode)], [Properties](types.md#paho.mqtt.properties.Properties) | None], None] | None*

The callback called when the broker responds to a subscribe
request.

Expected signature for callback API version 2:

```default
subscribe_callback(client, userdata, mid, reason_code_list, properties)
```

Expected signature for callback API version 1 change with MQTT protocol version:
: * For MQTT v3.1 and v3.1.1 it’s:
    ```default
    subscribe_callback(client, userdata, mid, granted_qos)
    ```
  * For MQTT v5.0 it’s:
    ```default
    subscribe_callback(client, userdata, mid, reason_code_list, properties)
    ```

* **Parameters:**
  * **client** ([*Client*](#paho.mqtt.client.Client)) – the client instance for this callback
  * **userdata** – the private user data as set in Client() or user_data_set()
  * **mid** (*int*) – matches the mid variable returned from the corresponding
    subscribe() call.
  * **reason_code_list** (*list* *[*[*ReasonCode*](types.md#paho.mqtt.reasoncodes.ReasonCode) *]*) – reason codes received from the broker for each subscription.
    In MQTT v5.0 it’s the reason code defined by the standard.
    In MQTT v3, we convert granted QoS to a reason code.
    It’s a list of ReasonCode instances.
  * **properties** ([*Properties*](types.md#paho.mqtt.properties.Properties)) – the MQTT v5.0 properties received from the broker.
    For MQTT v3.1 and v3.1.1 properties is not provided and an empty Properties
    object is always used.
  * **granted_qos** (*list* *[**int* *]*) – list of integers that give the QoS level the broker has
    granted for each of the different subscription requests.

Decorator: @client.subscribe_callback() (`client` is the name of the
: instance which this callback is being attached to)

#### *property* on_unsubscribe *: Callable[[[Client](#paho.mqtt.client.Client), Any, int], None] | Callable[[[Client](#paho.mqtt.client.Client), Any, int, [Properties](types.md#paho.mqtt.properties.Properties), [ReasonCode](types.md#paho.mqtt.reasoncodes.ReasonCode) | List[[ReasonCode](types.md#paho.mqtt.reasoncodes.ReasonCode)]], None] | Callable[[[Client](#paho.mqtt.client.Client), Any, int, List[[ReasonCode](types.md#paho.mqtt.reasoncodes.ReasonCode)], [Properties](types.md#paho.mqtt.properties.Properties) | None], None] | None*

The callback called when the broker responds to an unsubscribe
request.

Expected signature for callback API version 2:

```default
unsubscribe_callback(client, userdata, mid, reason_code_list, properties)
```

Expected signature for callback API version 1 change with MQTT protocol version:
: * For MQTT v3.1 and v3.1.1 it’s:
    ```default
    unsubscribe_callback(client, userdata, mid)
    ```
  * For MQTT v5.0 it’s:
    ```default
    unsubscribe_callback(client, userdata, mid, properties, v1_reason_codes)
    ```

* **Parameters:**
  * **client** ([*Client*](#paho.mqtt.client.Client)) – the client instance for this callback
  * **userdata** – the private user data as set in Client() or user_data_set()
  * **mid** – matches the mid variable returned from the corresponding
    unsubscribe() call.
  * **reason_code_list** (*list* *[*[*ReasonCode*](types.md#paho.mqtt.reasoncodes.ReasonCode) *]*) – reason codes received from the broker for each unsubscription.
    In MQTT v5.0 it’s the reason code defined by the standard.
    In MQTT v3, there is not equivalent from broken and empty list
    is always used.
  * **properties** ([*Properties*](types.md#paho.mqtt.properties.Properties)) – the MQTT v5.0 properties received from the broker.
    For MQTT v3.1 and v3.1.1 properties is not provided and an empty Properties
    object is always used.
  * **v1_reason_codes** – the MQTT v5.0 reason codes received from the broker for each
    unsubscribe topic.  A list of ReasonCode instances OR a single
    ReasonCode when we unsubscribe from a single topic.

Decorator: @client.unsubscribe_callback() (`client` is the name of the
: instance which this callback is being attached to)

#### *property* password *: str | None*

The password used to connect to the MQTT broker, or None if no password is used.

This property may not be changed if the connection is already open.

#### *property* port *: int*

Broker TCP port to connect to.

This property may not be changed if the connection is already open.

#### *property* protocol *: [MQTTProtocolVersion](types.md#paho.mqtt.enums.MQTTProtocolVersion)*

Protocol version used (MQTT v3, MQTT v3.11, MQTTv5)

This property is read-only.

#### proxy_set(\*\*proxy_args: Any)

Configure proxying of MQTT connection. Enables support for SOCKS or
HTTP proxies.

Proxying is done through the PySocks library. Brief descriptions of the
proxy_args parameters are below; see the PySocks docs for more info.

(Required)

* **Parameters:**
  * **proxy_type** – One of {socks.HTTP, socks.SOCKS4, or socks.SOCKS5}
  * **proxy_addr** – IP address or DNS name of proxy server

(Optional)

* **Parameters:**
  * **proxy_port** – (int) port number of the proxy server. If not provided,
    the PySocks package default value will be utilized, which differs by proxy_type.
  * **proxy_rdns** – boolean indicating whether proxy lookup should be performed
    remotely (True, default) or locally (False)
  * **proxy_username** – username for SOCKS5 proxy, or userid for SOCKS4 proxy
  * **proxy_password** – password for SOCKS5 proxy

Example:

```default
mqttc.proxy_set(proxy_type=socks.HTTP, proxy_addr='1.2.3.4', proxy_port=4231)
```

#### publish(topic: str, payload: str | bytes | bytearray | int | float | None = None, qos: int = 0, retain: bool = False, properties: [Properties](types.md#paho.mqtt.properties.Properties) | None = None)

Publish a message on a topic.

This causes a message to be sent to the broker and subsequently from
the broker to any clients subscribing to matching topics.

* **Parameters:**
  * **topic** (*str*) – The topic that the message should be published on.
  * **payload** – The actual message to send. If not given, or set to None a
    zero length message will be used. Passing an int or float will result
    in the payload being converted to a string representing that number. If
    you wish to send a true int/float, use struct.pack() to create the
    payload you require.
  * **qos** (*int*) – The quality of service level to use.
  * **retain** (*bool*) – If set to true, the message will be set as the “last known
    good”/retained message for the topic.
  * **properties** ([*Properties*](types.md#paho.mqtt.properties.Properties)) – (MQTT v5.0 only) the MQTT v5.0 properties to be included.

Returns a [`MQTTMessageInfo`](#paho.mqtt.client.MQTTMessageInfo) class, which can be used to determine whether
the message has been delivered (using [`is_published()`](#paho.mqtt.client.MQTTMessageInfo.is_published)) or to block
waiting for the message to be delivered ([`wait_for_publish()`](#paho.mqtt.client.MQTTMessageInfo.wait_for_publish)). The
message ID and return code of the publish() call can be found at
[`info.mid`](#paho.mqtt.client.MQTTMessage.mid) and `info.rc`.

For backwards compatibility, the [`MQTTMessageInfo`](#paho.mqtt.client.MQTTMessageInfo) class is iterable so
the old construct of `(rc, mid) = client.publish(...)` is still valid.

rc is MQTT_ERR_SUCCESS to indicate success or MQTT_ERR_NO_CONN if the
client is not currently connected.  mid is the message ID for the
publish request. The mid value can be used to track the publish request
by checking against the mid argument in the on_publish() callback if it
is defined.

* **Raises:**
  * **ValueError** – if topic is None, has zero length or is
    invalid (contains a wildcard), except if the MQTT version used is v5.0.
    For v5.0, a zero length topic can be used when a Topic Alias has been set.
  * **ValueError** – if qos is not one of 0, 1 or 2
  * **ValueError** – if the length of the payload is greater than 268435455 bytes.

#### reconnect()

Reconnect the client after a disconnect. Can only be called after
connect()/connect_async().

#### reconnect_delay_set(min_delay: int = 1, max_delay: int = 120)

Configure the exponential reconnect delay

When connection is lost, wait initially min_delay seconds and
double this time every attempt. The wait is capped at max_delay.
Once the client is fully connected (e.g. not only TCP socket, but
received a success CONNACK), the wait timer is reset to min_delay.

#### reinitialise(client_id: str = '', clean_session: bool = True, userdata: Any = None)

#### socket()

Return the socket or ssl object for this client.

#### subscribe(topic: str | tuple[str, int] | tuple[str, SubscribeOptions] | list[tuple[str, int]] | list[tuple[str, SubscribeOptions]], qos: int = 0, options: SubscribeOptions | None = None, properties: [Properties](types.md#paho.mqtt.properties.Properties) | None = None)

Subscribe the client to one or more topics.

This function may be called in three different ways (and a further three for MQTT v5.0):

### Simple string and integer

e.g. subscribe(“my/topic”, 2)

* **topic:**
  A string specifying the subscription topic to subscribe to.
* **qos:**
  The desired quality of service level for the subscription.
  Defaults to 0.
* **options and properties:**
  Not used.

### Simple string and subscribe options (MQTT v5.0 only)

e.g. subscribe(“my/topic”, options=SubscribeOptions(qos=2))

* **topic:**
  A string specifying the subscription topic to subscribe to.
* **qos:**
  Not used.
* **options:**
  The MQTT v5.0 subscribe options.
* **properties:**
  a Properties instance setting the MQTT v5.0 properties
  to be included. Optional - if not set, no properties are sent.

### String and integer tuple

e.g. subscribe((“my/topic”, 1))

* **topic:**
  A tuple of (topic, qos). Both topic and qos must be present in
  the tuple.
* **qos and options:**
  Not used.
* **properties:**
  Only used for MQTT v5.0.  A Properties instance setting the
  MQTT v5.0 properties. Optional - if not set, no properties are sent.

### String and subscribe options tuple (MQTT v5.0 only)

e.g. subscribe((“my/topic”, SubscribeOptions(qos=1)))

* **topic:**
  A tuple of (topic, SubscribeOptions). Both topic and subscribe
  options must be present in the tuple.
* **qos and options:**
  Not used.
* **properties:**
  a Properties instance setting the MQTT v5.0 properties
  to be included. Optional - if not set, no properties are sent.

### List of string and integer tuples

e.g. subscribe([(“my/topic”, 0), (“another/topic”, 2)])

This allows multiple topic subscriptions in a single SUBSCRIPTION
command, which is more efficient than using multiple calls to
subscribe().

* **topic:**
  A list of tuple of format (topic, qos). Both topic and qos must
  be present in all of the tuples.
* **qos, options and properties:**
  Not used.

### List of string and subscribe option tuples (MQTT v5.0 only)

e.g. subscribe([(“my/topic”, SubscribeOptions(qos=0), (“another/topic”, SubscribeOptions(qos=2)])

This allows multiple topic subscriptions in a single SUBSCRIPTION
command, which is more efficient than using multiple calls to
subscribe().

* **topic:**
  A list of tuple of format (topic, SubscribeOptions). Both topic and subscribe
  options must be present in all of the tuples.
* **qos and options:**
  Not used.
* **properties:**
  a Properties instance setting the MQTT v5.0 properties
  to be included. Optional - if not set, no properties are sent.

The function returns a tuple (result, mid), where result is
MQTT_ERR_SUCCESS to indicate success or (MQTT_ERR_NO_CONN, None) if the
client is not currently connected.  mid is the message ID for the
subscribe request. The mid value can be used to track the subscribe
request by checking against the mid argument in the on_subscribe()
callback if it is defined.

Raises a ValueError if qos is not 0, 1 or 2, or if topic is None or has
zero string length, or if topic is not a string, tuple or list.

#### tls_insecure_set(value: bool)

Configure verification of the server hostname in the server certificate.

If value is set to true, it is impossible to guarantee that the host
you are connecting to is not impersonating your server. This can be
useful in initial server testing, but makes it possible for a malicious
third party to impersonate your server through DNS spoofing, for
example.

Do not use this function in a real system. Setting value to true means
there is no point using encryption.

Must be called before [`connect()`](#paho.mqtt.client.Client.connect) and after either [`tls_set()`](#paho.mqtt.client.Client.tls_set) or
[`tls_set_context()`](#paho.mqtt.client.Client.tls_set_context).

#### tls_set(ca_certs: str | None = None, certfile: str | None = None, keyfile: str | None = None, cert_reqs: VerifyMode | None = None, tls_version: int | None = None, ciphers: str | None = None, keyfile_password: str | None = None, alpn_protocols: list[str] | None = None)

Configure network encryption and authentication options. Enables SSL/TLS support.

* **Parameters:**
  * **ca_certs** (*str*) – 

    a string path to the Certificate Authority certificate files
    that are to be treated as trusted by this client. If this is the only
    option given then the client will operate in a similar manner to a web
    browser. That is to say it will require the broker to have a
    certificate signed by the Certificate Authorities in ca_certs and will
    communicate using TLS v1,2, but will not attempt any form of
    authentication. This provides basic network encryption but may not be
    sufficient depending on how the broker is configured.

    By default, on Python 2.7.9+ or 3.4+, the default certification
    authority of the system is used. On older Python version this parameter
    is mandatory.
  * **certfile** (*str*) – PEM encoded client certificate filename. Used with
    keyfile for client TLS based authentication. Support for this feature is
    broker dependent. Note that if the files in encrypted and needs a password to
    decrypt it, then this can be passed using the keyfile_password argument - you
    should take precautions to ensure that your password is
    not hard coded into your program by loading the password from a file
    for example. If you do not provide keyfile_password, the password will
    be requested to be typed in at a terminal window.
  * **keyfile** (*str*) – PEM encoded client private keys filename. Used with
    certfile for client TLS based authentication. Support for this feature is
    broker dependent. Note that if the files in encrypted and needs a password to
    decrypt it, then this can be passed using the keyfile_password argument - you
    should take precautions to ensure that your password is
    not hard coded into your program by loading the password from a file
    for example. If you do not provide keyfile_password, the password will
    be requested to be typed in at a terminal window.
  * **cert_reqs** – the certificate requirements that the client imposes
    on the broker to be changed. By default this is ssl.CERT_REQUIRED,
    which means that the broker must provide a certificate. See the ssl
    pydoc for more information on this parameter.
  * **tls_version** – the version of the SSL/TLS protocol used to be
    specified. By default TLS v1.2 is used. Previous versions are allowed
    but not recommended due to possible security problems.
  * **ciphers** (*str*) – encryption ciphers that are allowed
    for this connection, or None to use the defaults. See the ssl pydoc for
    more information.

Must be called before [`connect()`](#paho.mqtt.client.Client.connect), [`connect_async()`](#paho.mqtt.client.Client.connect_async) or [`connect_srv()`](#paho.mqtt.client.Client.connect_srv).

#### tls_set_context(context: SSLContext | None = None)

Configure network encryption and authentication context. Enables SSL/TLS support.

* **Parameters:**
  **context** – an ssl.SSLContext object. By default this is given by
  `ssl.create_default_context()`, if available.

Must be called before [`connect()`](#paho.mqtt.client.Client.connect), [`connect_async()`](#paho.mqtt.client.Client.connect_async) or [`connect_srv()`](#paho.mqtt.client.Client.connect_srv).

#### *property* transport *: Literal['tcp', 'websockets']*

Transport method used for the connection (“tcp” or “websockets”).

This property may not be changed if the connection is already open.

#### unsubscribe(topic: str, properties: [Properties](types.md#paho.mqtt.properties.Properties) | None = None)

Unsubscribe the client from one or more topics.

* **Parameters:**
  * **topic** – A single string, or list of strings that are the subscription
    topics to unsubscribe from.
  * **properties** – (MQTT v5.0 only) a Properties instance setting the MQTT v5.0 properties
    to be included. Optional - if not set, no properties are sent.

Returns a tuple (result, mid), where result is MQTT_ERR_SUCCESS
to indicate success or (MQTT_ERR_NO_CONN, None) if the client is not
currently connected.
mid is the message ID for the unsubscribe request. The mid value can be
used to track the unsubscribe request by checking against the mid
argument in the on_unsubscribe() callback if it is defined.

* **Raises:**
  **ValueError** – if topic is None or has zero string length, or is
  not a string or list.

#### user_data_get()

Get the user data variable passed to callbacks. May be any data type.

#### user_data_set(userdata: Any)

Set the user data variable passed to callbacks. May be any data type.

#### *property* username *: str | None*

The username used to connect to the MQTT broker, or None if no username is used.

This property may not be changed if the connection is already open.

#### username_pw_set(username: str | None, password: str | None = None)

Set a username and optionally a password for broker authentication.

Must be called before connect() to have any effect.
Requires a broker that supports MQTT v3.1 or more.

* **Parameters:**
  * **username** (*str*) – The username to authenticate with. Need have no relationship to the client id. Must be str
    [MQTT-3.1.3-11].
    Set to None to reset client back to not using username/password for broker authentication.
  * **password** (*str*) – The password to authenticate with. Optional, set to None if not required. If it is str, then it
    will be encoded as UTF-8.

#### want_write()

Call to determine if there is network data waiting to be written.
Useful if you are calling select() yourself rather than using [`loop()`](#paho.mqtt.client.Client.loop), [`loop_start()`](#paho.mqtt.client.Client.loop_start) or [`loop_forever()`](#paho.mqtt.client.Client.loop_forever).

#### will_clear()

Removes a will that was previously configured with [`will_set()`](#paho.mqtt.client.Client.will_set).

Must be called before connect() to have any effect.

#### *property* will_payload *: bytes | None*

The payload for the will message that is sent when disconnecting unexpectedly. None if a will shall not be sent.

This property is read-only. Use [`will_set()`](#paho.mqtt.client.Client.will_set) to change its value.

#### will_set(topic: str, payload: str | bytes | bytearray | int | float | None = None, qos: int = 0, retain: bool = False, properties: [Properties](types.md#paho.mqtt.properties.Properties) | None = None)

Set a Will to be sent by the broker in case the client disconnects unexpectedly.

This must be called before connect() to have any effect.

* **Parameters:**
  * **topic** (*str*) – The topic that the will message should be published on.
  * **payload** – The message to send as a will. If not given, or set to None a
    zero length message will be used as the will. Passing an int or float
    will result in the payload being converted to a string representing
    that number. If you wish to send a true int/float, use struct.pack() to
    create the payload you require.
  * **qos** (*int*) – The quality of service level to use for the will.
  * **retain** (*bool*) – If set to true, the will message will be set as the “last known
    good”/retained message for the topic.
  * **properties** ([*Properties*](types.md#paho.mqtt.properties.Properties)) – (MQTT v5.0 only) the MQTT v5.0 properties
    to be included with the will message. Optional - if not set, no properties are sent.
* **Raises:**
  **ValueError** – if qos is not 0, 1 or 2, or if topic is None or has
  zero string length.

See [`will_clear`](#paho.mqtt.client.Client.will_clear) to clear will. Note that will are NOT send if the client disconnect cleanly
for example by calling [`disconnect()`](#paho.mqtt.client.Client.disconnect).

#### *property* will_topic *: str | None*

The topic name a will message is sent to when disconnecting unexpectedly. None if a will shall not be sent.

This property is read-only. Use [`will_set()`](#paho.mqtt.client.Client.will_set) to change its value.

#### ws_set_options(path: str = '/mqtt', headers: Callable[[Dict[str, str]], Dict[str, str]] | Dict[str, str] | None = None)

Set the path and headers for a websocket connection

* **Parameters:**
  * **path** (*str*) – a string starting with / which should be the endpoint of the
    mqtt connection on the remote server
  * **headers** – can be either a dict or a callable object. If it is a dict then
    the extra items in the dict are added to the websocket headers. If it is
    a callable, then the default websocket headers are passed into this
    function and the result is used as the new headers.

### *class* paho.mqtt.client.ConnectFlags(session_present: bool)

Contains additional information passed to [`on_connect`](#paho.mqtt.client.Client.on_connect) callback

#### session_present *: bool*

this flag is useful for clients that are
using clean session set to False only (MQTTv3) or clean_start = False (MQTTv5).
In that case, if client  that reconnects to a broker that it has previously
connected to, this flag indicates whether the broker still has the
session information for the client. If true, the session still exists.

### *class* paho.mqtt.client.DisconnectFlags(is_disconnect_packet_from_server: bool)

Contains additional information passed to [`on_disconnect`](#paho.mqtt.client.Client.on_disconnect) callback

#### is_disconnect_packet_from_server *: bool*

tells whether this on_disconnect call is the result
of receiving an DISCONNECT packet from the broker or if the on_disconnect is only
generated by the client library.
When true, the reason code is generated by the broker.

### *class* paho.mqtt.client.MQTTMessage(mid: int = 0, topic: bytes = b'')

This is a class that describes an incoming message. It is
passed to the [`on_message`](#paho.mqtt.client.Client.on_message) callback as the message parameter.

#### dup

#### info

#### mid

The message id (int).

#### payload

the message payload (bytes)

#### properties *: [Properties](types.md#paho.mqtt.properties.Properties) | None*

In MQTT v5.0, the properties associated with the message. ([`Properties`](types.md#paho.mqtt.properties.Properties))

#### qos

The message Quality of Service (0, 1 or 2).

#### retain

If true, the message is a retained message and not fresh.

#### state

#### timestamp

#### *property* topic *: str*

topic that the message was published on.

This property is read-only.

### *class* paho.mqtt.client.MQTTMessageInfo(mid: int)

This is a class returned from [`Client.publish()`](#paho.mqtt.client.Client.publish) and can be used to find
out the mid of the message that was published, and to determine whether the
message has been published, and/or wait until it is published.

#### is_published()

Returns True if the message associated with this object has been
published, else returns False.

To wait for this to become true, look at [`wait_for_publish`](#paho.mqtt.client.MQTTMessageInfo.wait_for_publish).

#### mid

The message Id (int)

#### next()

#### rc *: [MQTTErrorCode](types.md#paho.mqtt.enums.MQTTErrorCode)*

The [`MQTTErrorCode`](types.md#paho.mqtt.enums.MQTTErrorCode) that give status for this message.
This value could change until the message [`is_published`](#paho.mqtt.client.MQTTMessageInfo.is_published)

#### wait_for_publish(timeout: float | None = None)

Block until the message associated with this object is published, or
until the timeout occurs. If timeout is None, this will never time out.
Set timeout to a positive number of seconds, e.g. 1.2, to enable the
timeout.

* **Raises:**
  * **ValueError** – if the message was not queued due to the outgoing
    queue being full.
  * **RuntimeError** – if the message was not published for another
    reason.

### *exception* paho.mqtt.client.WebsocketConnectionError

WebsocketConnectionError is a subclass of ConnectionError.

It’s raised when unable to perform the Websocket handshake.

### paho.mqtt.client.connack_string(connack_code: int | [ReasonCode](types.md#paho.mqtt.reasoncodes.ReasonCode))

Return the string associated with a CONNACK result or CONNACK reason code.

### paho.mqtt.client.convert_connack_rc_to_reason_code(connack_code: [ConnackCode](types.md#paho.mqtt.enums.ConnackCode))

Convert a MQTTv3 / MQTTv3.1.1 connack result to [`ReasonCode`](types.md#paho.mqtt.reasoncodes.ReasonCode).

This is used in [`on_connect`](#paho.mqtt.client.Client.on_connect) callback to have a consistent API.

Be careful that the numeric value isn’t the same, for example:

```pycon
>>> ConnackCode.CONNACK_REFUSED_SERVER_UNAVAILABLE == 3
>>> convert_connack_rc_to_reason_code(ConnackCode.CONNACK_REFUSED_SERVER_UNAVAILABLE) == 136
```

It’s recommended to compare by names

```pycon
>>> code_to_test = ReasonCode(PacketTypes.CONNACK, "Server unavailable")
>>> convert_connack_rc_to_reason_code(ConnackCode.CONNACK_REFUSED_SERVER_UNAVAILABLE) == code_to_test
```

### paho.mqtt.client.convert_disconnect_error_code_to_reason_code(rc: [MQTTErrorCode](types.md#paho.mqtt.enums.MQTTErrorCode))

Convert an MQTTErrorCode to Reason code.

This is used in [`on_disconnect`](#paho.mqtt.client.Client.on_disconnect) callback to have a consistent API.

Be careful that the numeric value isn’t the same, for example:

```pycon
>>> MQTTErrorCode.MQTT_ERR_PROTOCOL == 2
>>> convert_disconnect_error_code_to_reason_code(MQTTErrorCode.MQTT_ERR_PROTOCOL) == 130
```

It’s recommended to compare by names

```pycon
>>> code_to_test = ReasonCode(PacketTypes.DISCONNECT, "Protocol error")
>>> convert_disconnect_error_code_to_reason_code(MQTTErrorCode.MQTT_ERR_PROTOCOL) == code_to_test
```

### paho.mqtt.client.error_string(mqtt_errno: [MQTTErrorCode](types.md#paho.mqtt.enums.MQTTErrorCode))

Return the error string associated with an mqtt error number.

### paho.mqtt.client.topic_matches_sub(sub: str, topic: str)

Check whether a topic matches a subscription.

For example:

* Topic “foo/bar” would match the subscription “foo/#” or “+/bar”
* Topic “non/matching” would not match the subscription “non/+/+”
