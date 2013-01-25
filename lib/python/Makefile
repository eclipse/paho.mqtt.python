include ../../config.mk

# Set DESTDIR if it isn't given
DESTDIR?=/

.PHONY : all clean install

all : mosquitto.pyc

install : all
	python ./setup.py install --prefix=${prefix} --root=${DESTDIR}

mosquitto.pyc : mosquitto.py
	python ./setup.py build

clean :
	-rm -rf build mosquitto.pyc __pycache__
