from sys import version

from distutils.core import setup
setup(name='paho`',
	version='0.9.0',
	description='MQTT version 3.1 client class',
	author='Roger Light',
	author_email='roger@atchoo.org',
	url='http://eclipse.org/paho',
	# FIXME license='Eclipse Public License',
    package_dir={'': 'src'},
    packages=['paho', 'paho.mqtt'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        # FIXME 'License :: OSI Approved :: BSD License',
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
