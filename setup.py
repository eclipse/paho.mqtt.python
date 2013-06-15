from sys import version

from distutils.core import setup
setup(name='mosquitto',
	version='1.1.1',
	description='MQTT version 3.1 client class',
	author='Roger Light',
	author_email='roger@atchoo.org',
	url='http://mosquitto.org/',
	download_url='http://mosquitto.org/files/',
	license='BSD License',
	py_modules=['mosquitto'],

    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Communications',
        'Topic :: Internet',
        ]
	)
