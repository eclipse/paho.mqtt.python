.PHONY: all test
.NOTPARALLEL:

PYTHON?=python3

all :

test :
	$(PYTHON) ./01-asyncio.py python/01-asyncio.test
	$(PYTHON) ./01-decorators.py python/01-decorators.test
	$(PYTHON) ./01-keepalive-pingreq.py python/01-keepalive-pingreq.test
	$(PYTHON) ./01-no-clean-session.py python/01-no-clean-session.test
	$(PYTHON) ./01-reconnect-on-failure.py python/01-reconnect-on-failure.test
	$(PYTHON) ./01-unpwd-empty-password-set.py python/01-unpwd-empty-password-set.test
	$(PYTHON) ./01-unpwd-empty-set.py python/01-unpwd-empty-set.test
	$(PYTHON) ./01-unpwd-set.py python/01-unpwd-set.test
	$(PYTHON) ./01-unpwd-unicode-set.py python/01-unpwd-unicode-set.test
	$(PYTHON) ./01-will-set.py python/01-will-set.test
	$(PYTHON) ./01-will-unpwd-set.py python/01-will-unpwd-set.test
	$(PYTHON) ./01-zero-length-clientid.py python/01-zero-length-clientid.test
	$(PYTHON) ./02-subscribe-qos0.py python/02-subscribe-qos0.test
	$(PYTHON) ./02-subscribe-qos1.py python/02-subscribe-qos1.test
	$(PYTHON) ./02-subscribe-qos2.py python/02-subscribe-qos2.test
	$(PYTHON) ./02-unsubscribe.py python/02-unsubscribe.test
	$(PYTHON) ./03-publish-b2c-qos1.py python/03-publish-b2c-qos1.test
	$(PYTHON) ./03-publish-c2b-qos1-disconnect.py python/03-publish-c2b-qos1-disconnect.test
	$(PYTHON) ./03-publish-c2b-qos2-disconnect.py python/03-publish-c2b-qos2-disconnect.test
	$(PYTHON) ./03-publish-helper-qos0.py python/03-publish-helper-qos0.test
	$(PYTHON) ./03-publish-helper-qos0-v5.py python/03-publish-helper-qos0-v5.test
	$(PYTHON) ./03-publish-helper-qos1-disconnect.py python/03-publish-helper-qos1-disconnect.test
	$(PYTHON) ./03-publish-qos0-no-payload.py python/03-publish-qos0-no-payload.test
	$(PYTHON) ./03-publish-qos0.py python/03-publish-qos0.test
	$(PYTHON) ./04-retain-qos0.py python/04-retain-qos0.test
	$(PYTHON) ./08-ssl-bad-cacert.py python/08-ssl-bad-cacert.test
	$(PYTHON) ./08-ssl-connect-cert-auth-pw.py python/08-ssl-connect-cert-auth-pw.test
	$(PYTHON) ./08-ssl-connect-cert-auth.py python/08-ssl-connect-cert-auth.test
	$(PYTHON) ./08-ssl-connect-no-auth.py python/08-ssl-connect-no-auth.test
