#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='pimat',
    description='Raspberry Pi Multi Automation tool',
    version='0.3.0',
    url='https://github.com/jorgensoares/pimat',
    author='Jorge Soares',
    packages=find_packages(exclude=['tests']),
    entry_points={
        'console_scripts': [
            'pimat-server = pimat_server.__main__:main',
            'pimat-relay = pimat_server.relays:main',
            'pimat-web = pimat_web.app:main'
        ]
    },
    install_requires=['flask', 'flask-mysql','configparser', 'python-crontab', 'RPi.GPIO', 'adafruit_python_dht', 'flask_sqlalchemy'],
    package_data={'pimat_web': ['templates/*']}
)
