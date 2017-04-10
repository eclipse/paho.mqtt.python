__version__ = "1.3.0.dev0"

VERSION_MAJOR = 1
VERSION_MINOR = 3
VERSION_REVISION = 0
VERSION_NUMBER = (VERSION_MAJOR * 1000000 + VERSION_MINOR * 1000 + VERSION_REVISION)


class MQTTException(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)
