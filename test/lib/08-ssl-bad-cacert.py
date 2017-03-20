#!/usr/bin/env python

import context

context.check_ssl()

rc = 1

client = context.start_client()

client.wait()

rc = client.returncode

exit(rc)
