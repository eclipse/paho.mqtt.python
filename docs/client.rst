client module
=============

..
   exclude-members exclude decorator for callback, because decorator are
   documented in there respective on_XXX

.. automodule:: paho.mqtt.client
   :members:
   :exclude-members: connect_callback, connect_fail_callback, disconnect_callback, log_callback,
      message_callback, topic_callback, pre_connect_callback, publish_callback,
      socket_close_callback, socket_open_callback, socket_register_write_callback,
      socket_unregister_write_callback, subscribe_callback, unsubscribe_callback
   :undoc-members:
