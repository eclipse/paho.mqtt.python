#!/bin/bash -e

#######################################################
# Script that will setup the build environment for
# building the paho python client libraries
#######################################################

NAME=paho-mqtt-python
VERSION=1.1.1


function setupDirectories
{
	rm -fR debian
	mkdir -p debian/DEBIAN
	mkdir -p debian/usr/share/doc/${NAME}/
	mkdir -p debian/usr/share/pyshared/${NAME}/
	mkdir -p debian/usr/share/python-support/
}

function copySource
{
	cp ../src/paho/mqtt/* debian/usr/share/pyshared/${NAME}/

}

function documentationCopy
{
	cp control debian/DEBIAN/ 
	cp ../copyright debian/usr/share/doc/${NAME}/copyright
	gzip -n -9 -c ../ChangeLog.txt > debian/usr/share/doc/${NAME}/changelog.gz
	gzip -n -9 -c ../changelog.Debian > debian/usr/share/doc/${NAME}/changelog.Debian.gz
}


setupDirectories
documentationCopy
copySource

find ./debian -type d | xargs chmod 755

fakeroot dpkg-deb --build debian
mv debian.deb ${NAME}.${VERSION}.deb
lintian ${NAME}.${VERSION}.deb 
