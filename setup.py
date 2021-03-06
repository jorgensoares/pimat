#!/usr/bin/env python
from setuptools import setup, find_packages
from distutils.util import convert_path

main_ns = {}
ver_path = convert_path('pimat_web/version.py')
with open(ver_path) as ver_file:
    exec(ver_file.read(), main_ns)

setup(
    name='pimat',
    description='Raspberry Pi Multi Automation tool',
    version=main_ns['__version__'],
    url='https://github.com/jorgensoares/pimat',
    author='Jorge Soares',
    packages=find_packages(exclude=['tests']),
    entry_points={
        'console_scripts': [
            'pimat-relay = pimat_relays.__main__:main',
            'pimat-relay-api = pimat_relays.api:main',
            'pimat-sensors = pimat_sensors.__main__:main',
            'pimat-monitoring = pimat_monitoring.__main__:main',
            'pimat-web = pimat_web.app:main'
        ]
    },
    install_requires=['flask',
                      'configparser',
                      'python-crontab',
                      'RPi.GPIO',
                      'adafruit_python_dht',
                      'flask_sqlalchemy',
                      'MySQL-python',
                      'flask-login',
                      'flask-restful',
                      'requests',
                      'werkzeug',
                      'itsdangerous',
                      'Flask-Mail',
                      'Flask-WTF',
                      'Flask-Principal',
                      'psutil', 'pytz'],

    include_package_data=True,
    zip_safe=False,
)
