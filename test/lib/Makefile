.PHONY: all test
.NOTPARALLEL:

all :

test :
	python ./01-will-set.py python/01-will-set.test
	python ./01-unpwd-set.py python/01-unpwd-set.test
	python ./01-unpwd-unicode-set.py python/01-unpwd-unicode-set.test
	python ./01-unpwd-empty-password-set.py python/01-unpwd-empty-password-set.test
	python ./01-unpwd-empty-set.py python/01-unpwd-empty-set.test
	python ./01-will-unpwd-set.py python/01-will-unpwd-set.test
	python ./01-zero-length-clientid.py python/01-zero-length-clientid.test
	python ./01-no-clean-session.py python/01-no-clean-session.test
	python ./01-keepalive-pingreq.py python/01-keepalive-pingreq.test
	python ./02-subscribe-qos0.py python/02-subscribe-qos0.test
	python ./02-subscribe-qos1.py python/02-subscribe-qos1.test
	python ./02-subscribe-qos2.py python/02-subscribe-qos2.test
	python ./02-unsubscribe.py python/02-unsubscribe.test
	python ./03-publish-qos0.py python/03-publish-qos0.test
	python ./03-publish-qos0-no-payload.py python/03-publish-qos0-no-payload.test
	python ./03-publish-c2b-qos1-timeout.py python/03-publish-c2b-qos1-timeout.test
	python ./03-publish-c2b-qos1-disconnect.py python/03-publish-c2b-qos1-disconnect.test
	python ./03-publish-c2b-qos2-timeout.py python/03-publish-c2b-qos2-timeout.test
	python ./03-publish-c2b-qos2-disconnect.py python/03-publish-c2b-qos2-disconnect.test
	python ./03-publish-b2c-qos1.py python/03-publish-b2c-qos1.test
	python ./03-publish-b2c-qos2.py python/03-publish-b2c-qos2.test
	python ./03-publish-helper-qos0.py python/03-publish-helper-qos0.test
	python ./03-publish-helper-qos1-disconnect.py python/03-publish-helper-qos1-disconnect.test
	python ./04-retain-qos0.py python/04-retain-qos0.test
	python ./08-ssl-connect-no-auth.py python/08-ssl-connect-no-auth.test
	python ./08-ssl-connect-cert-auth.py python/08-ssl-connect-cert-auth.test
	python ./08-ssl-bad-cacert.py python/08-ssl-bad-cacert.test
