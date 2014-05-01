# Set DESTDIR if it isn't given
DESTDIR?=/

.PHONY : all clean install test python python3 upload

all :
	python ./setup.py build

install : all
	python ./setup.py install --root=${DESTDIR}

clean :
	-rm -rf build/ src/paho/mqtt/__pycache__ src/paho/mqtt/*.pyc src/paho/__pycache__ src/paho/*.pyc

python :
	$(MAKE) -C test python

python3 :
	$(MAKE) -C test python3

test : python python3

upload : test
	python ./setup.py sdist upload
