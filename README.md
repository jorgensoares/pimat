Introduction
============

**piMAT** -- Raspebrrypi Multi Automation Tool

A Lot of work in progress!!


## Documentation & Installation Guide

apt-get install python-pip python-dev libmysqlclient-dev python-smbus i2c-tools

sudo raspi-config
    --> Adanced options --> A7 I2C --> <yes> (enable) --> <yes>

If file exists
sudo nano /boot/config.txt

    Do:
        dtparam=i2c1=on
        dtparam=i2c_arm=on


sudo i2cdetect -y 1



### Contribution


### License

MIT


### Change log
