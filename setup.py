#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='pimat',
    description='Raspberry Pi Multi Automation tool',
    version='0.0.2',
    url='https://github.com/jorgensoares/pimat',
    author='Jorge Soares',
    packages=find_packages(exclude=['tests']),
    entry_points={
        'console_scripts': [
            'pimat_server = pimat-server.__main__:main',
            'pimat_web = pimat-web.app:main'
        ]
    },
    install_requires=['flask', 'configparser', 'python-crontab', 'RPi.GPIO', 'adafruit_python_dht'],
    package_data={'pimat_web': ['templates/*']}
)