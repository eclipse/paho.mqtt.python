# -*- coding: utf-8 -*-

import sys
import os
import subprocess

try:
    import ssl
except ImportError:
    ssl = None

# Ensure can import paho_test package
try:
    import paho_test

except ImportError:
    # This part is only required when paho_test module is not on Python path
    # From http://stackoverflow.com/questions/279237/python-import-a-module-from-a-folder
    import inspect

    cmd_subfolder = os.path.realpath(
        os.path.abspath(
            os.path.join(
                os.path.split(
                    inspect.getfile(inspect.currentframe())
                )[0],
                "..",
            )
        )
    )
    if cmd_subfolder not in sys.path:
        sys.path.insert(0, cmd_subfolder)

    import paho_test

env = dict(os.environ)
pp = env.get('PYTHONPATH', '')
env['PYTHONPATH'] = '../../src' + os.pathsep + pp


def start_client():
    args = [sys.executable, ] + sys.argv[1:]
    client = subprocess.Popen(args, env=env)
    return client


def check_ssl():
    if ssl is None:
        print("WARNING: SSL not available in current environment")
        exit(0)

    if not hasattr(ssl, 'SSLContext'):
        print("WARNING: SSL without SSLContext is not supported")
        exit(0)
