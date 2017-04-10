#!/usr/bin/env python

import context

rc = 1

client = context.start_client()

client.wait()

exit(client.returncode)
