#!/usr/bin/env python3

import context

context.check_ssl()

rc = 1

client = context.start_client()

client.wait()

rc = client.returncode

exit(rc)
