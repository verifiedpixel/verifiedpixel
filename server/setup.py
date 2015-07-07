#!/usr/bin/env python

from setuptools import setup, find_packages

LONG_DESCRIPTION = open('README.md').read()

setup(
    name='Verifiedpixel-Server',
    version='3.0-dev',
    description='Verifiedpixel REST API server',
    long_description=LONG_DESCRIPTION,
    author='Mark Lewis',
    author_email='mark.lewis@sourcefabric.org',
    url='https://github.com/verifiedpixel/verifiedpixel',
    license='GPLv3',
    platforms=['any'],
    packages=find_packages(),
    install_requires=[
        'Eve>=0.6',
        'Eve-Elastic>=0.2.10',
        'Flask>=0.10,<0.11',
        'Flask-Mail>=0.9.0,<0.10',
        'Flask-Script==2.0.5,<2.1',
        'Flask-PyMongo>=0.3.1',
        'autobahn[asyncio]>=0.10.4',
        'celery[redis]>=3.1.18',
        'bcrypt>=1.1.1',
        'blinker>=1.3',
    ],
    scripts=['settings.py', 'app.py', 'wsgi.py', 'ws.py', 'manage.py'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ]
)
