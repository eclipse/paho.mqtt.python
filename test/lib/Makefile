.PHONY: all test
.NOTPARALLEL:

all :

test :
	./01-con-discon-success.py python/01-con-discon-success.test
	./01-con-discon-success-mqtt311.py python/01-con-discon-success-mqtt311.test
	./01-will-set.py python/01-will-set.test
	./01-unpwd-set.py python/01-unpwd-set.test
	./01-will-unpwd-set.py python/01-will-unpwd-set.test
	./01-zero-length-clientid.py python/01-zero-length-clientid.test
	./01-no-clean-session.py python/01-no-clean-session.test
	./01-keepalive-pingreq.py python/01-keepalive-pingreq.test
	./02-subscribe-qos0.py python/02-subscribe-qos0.test
	./02-subscribe-qos1.py python/02-subscribe-qos1.test
	./02-subscribe-qos2.py python/02-subscribe-qos2.test
	./02-unsubscribe.py python/02-unsubscribe.test
	./03-publish-qos0.py python/03-publish-qos0.test
	./03-publish-qos0-no-payload.py python/03-publish-qos0-no-payload.test
	./03-publish-c2b-qos1-timeout.py python/03-publish-c2b-qos1-timeout.test
	./03-publish-c2b-qos1-disconnect.py python/03-publish-c2b-qos1-disconnect.test
	./03-publish-c2b-qos2-timeout.py python/03-publish-c2b-qos2-timeout.test
	./03-publish-c2b-qos2-disconnect.py python/03-publish-c2b-qos2-disconnect.test
	./03-publish-b2c-qos1.py python/03-publish-b2c-qos1.test
	./03-publish-b2c-qos2.py python/03-publish-b2c-qos2.test
	./04-retain-qos0.py python/04-retain-qos0.test
	./08-ssl-connect-no-auth.py python/08-ssl-connect-no-auth.test
	./08-ssl-connect-cert-auth.py python/08-ssl-connect-cert-auth.test
	./08-ssl-bad-cacert.py python/08-ssl-bad-cacert.test
	./09-util-topic-matching.py python/09-util-topic-matching.test
