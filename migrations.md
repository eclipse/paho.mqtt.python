# Migration

## Change between version 1.x and 2.0

### Improved typing

Version 2.0 improved typing, but this would be compatible with existing code.
The most likely issue are some integer that are now better type, like `dup` on MQTTMessage.

That means that code that used `if msg.dup == 1:` will need to be change to `if msg.dup:` (the later version
for with both paho-mqtt 1.x and 2.0).

### Versioned the user callbacks

Version 2.0 of paho-mqtt introduced versioning of user-callback. To fix some inconsistency in callback
arguments and to provide better support for MQTTv5, version 2.0 changed the arguments passed to user-callback.

You can still use old version of callback, you are just require to tell paho-mqtt that you opt for this
version. For that just change your client creation from:
```
# OLD code
>>> mqttc = mqtt.Client()

# NEW code
>>> mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
```

That it, remaining of the code could stay unchanged.

The version 1 of callback is deprecated, but is still supported in version 2.x. If you want to upgrade to newer version of API callback, you will need to update your callbacks:

#### on_connect

```
# OLD code for MQTTv3
def on_connect(client, userdata, flags, rc):
    if flags["session present"] == 1:
        # ...
    if rc == 0:
        # success connect
    if rc > 0:
        # error processing

# OLD code for MQTTv5
def on_connect(client, userdata, flags, reason_code, properties):
    if flags["session present"] == 1:
        # ...
    if reason_code == 0:
        # success connect

# NEW code for both version
def on_connect(client, userdata, flags, reason_code, properties):
    if flags.session_present:
        # ...
    if reason_code == 0:
        # success connect
    if reason_code > 0:
        # error processing
```

Be careful that for MQTTv3, `rc` (an integer) changed to `reason_code` (an instance of ReasonCodes), and the numeric value changed.
The numeric value 0 means success for both, so as in above example, using `reason_code == 0`, `reason_code != 0` or other comparison with zero
is fine.
But if you had comparison with other value, you will need to update the code. It's recommended to compare to string value:

```
# OLD code for MQTTv3
def on_connect(client, userdata, flags, rc):
    if rc == 1:
        # handle bad protocol version
    if rc == CONNACK_REFUSED_IDENTIFIER_REJECTED:
        # handle bad identifier

# NEW code
def on_connect(client, userdata, flags, reason_code, properties):
    if rc == "Unsupported protocol version":
        # handle bad protocol version
    if rc == "Client identifier not valid":
        # handle bad identifier
```

#### on_disconnect

```
# OLD code for MQTTv3
def on_disconnect(client, userdata, rc):
    if rc == 0:
        # success disconnect
    if rc > 0:
        # error processing

# OLD code for MQTTv5
def on_disconnect(client, userdata, reason_code, properties):
    if reason_code:
        # error processing

# NEW code for both version
def on_disconnect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        # success disconnect
    if reason_code > 0:
        # error processing
```


#### on_subscribe

```
# OLD code for MQTTv3
def on_subscribe(client, userdata, mid, granted_qos):
    for sub_result in granted_qos:
        if sub_result == 1:
            # process QoS == 1
        if sub_result == 0x80:
            # error processing

# OLD code for MQTTv5
def on_disconnect(client, userdata, mid, reason_codes, properties):
    for sub_result in reason_codes:
        if sub_result == 1:
            # process QoS == 1
        # Any reason code >= 128 is a failure.
        if sub_result >= 128:
            # error processing

# NEW code for both version
def on_subscribe(client, userdata, mid, reason_codes, properties):
    for sub_result in reason_codes:
        if sub_result == 1:
            # process QoS == 1
        # Any reason code >= 128 is a failure.
        if sub_result >= 128:
            # error processing
```


#### on_unsubscribe

```
# OLD code for MQTTv3
def on_unsubscribe(client, userdata, mid):
    # ...

# OLD code for MQTTv5
def on_unsubscribe(client, userdata, mid, properties, reason_codes):
    # In OLD version, reason_codes could be a list or a single ReasonCodes object
    if isinstance(reason_codes, list):
        for unsub_result in reason_codes:
            # Any reason code >= 128 is a failure.
            if reason_codes[0] >= 128:
                # error processing
    else:
        # Any reason code >= 128 is a failure.
        if reason_codes > 128:
            # error processing


# NEW code for both version
def on_subscribe(client, userdata, mid, reason_codes, properties):
    # In NEW version, reason_codes is always a list. Empty for MQTTv3
    for unsub_result in reason_codes:
        # Any reason code >= 128 is a failure.
        if reason_codes[0] >= 128:
            # error processing
```


#### on_publish

```
# OLD code
def on_publish(client, userdata, mid):
    # ...


# NEW code
def on_publish(client, userdata, mid, reason_codes, properties):
    # ...
```


#### on_message

No change for this callback.
```
# OLD & NEW code
def on_message(client, userdata, message):
    # ...
```