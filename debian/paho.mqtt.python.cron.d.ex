#
# Regular cron jobs for the paho.mqtt.python package
#
0 4	* * *	root	[ -x /usr/bin/paho.mqtt.python_maintenance ] && /usr/bin/paho.mqtt.python_maintenance
