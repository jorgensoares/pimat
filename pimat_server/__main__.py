#!/usr/bin/python
import datetime
import logging
import signal
import sys
import time
import Adafruit_DHT
import RPi.GPIO as GPIO
import configparser
import scheduler
from relays import Relays
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Bind the DB engine to the metadata of the Base class
Base = declarative_base()


class Schedules(Base):

    __tablename__ = 'schedules'

    id = Column('id', Integer, primary_key=True)
    relay = Column(String(10))
    switch = Column(String(50))
    start_time = Column(String(5))
    stop_time = Column(String(5))
    enabled = Column(String(10))


class Sensors(Base):

    __tablename__ = 'sensors'

    id = Column('id', Integer, primary_key=True)
    timestamp = Column(DateTime)
    temperature1 = Column(Float)
    temperature2 = Column(Float)
    humidity = Column(Float)
    light1 = Column(Float)
    pressure = Column(Float)
    altitude = Column(Float)
    source = Column(String(100))

    def __init__(self, temperature1, humidity, light1):
        self.timestamp = datetime.datetime.now()
        self.temperature1 = temperature1
        self.humidity = humidity
        self.light1 = light1
        self.source = 'pimat_server'


def get_now():
    # get the current date and time as a string
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def sigterm_handler(_signo, _stack_frame):
    # When sysvinit sends the TERM signal, cleanup before exiting.
    print("[" + get_now() + "] received signal {}, exiting...".format(_signo))
    GPIO.cleanup()
    scheduler.remove_all()
    sys.exit(0)


def rc_time(pin_to_circuit):
    count = 0

    # Output on the pin for
    GPIO.setup(pin_to_circuit, GPIO.OUT)
    GPIO.output(pin_to_circuit, GPIO.LOW)
    time.sleep(0.1)

    # Change the pin back to input
    GPIO.setup(pin_to_circuit, GPIO.IN)

    # Count until the pin goes high
    while GPIO.input(pin_to_circuit) == GPIO.LOW:
        count += 1

    return count


def main():
    relay_config = configparser.ConfigParser()
    relay_config.read('/opt/pimat/relays.ini')
    pimat_config = configparser.ConfigParser()
    pimat_config.read('/opt/pimat/config.ini')

    log = logging.getLogger()
    handler = logging.FileHandler('/var/log/pimat/sensors.log')
    formatter = logging.Formatter('[%(levelname)s] [%(asctime)-15s] [PID: %(process)d] [%(name)s] %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    engine = create_engine(pimat_config['database']['engine'])
    session = sessionmaker(bind=engine)
    db = session()

    # Clean stuff
    scheduler.remove_all()

    for relay in relay_config['pins']:
        for pin in relay_config['pins'][relay]:

            relay_object = Relays(relay, pin)
            relay_object.set_mode()
            time.sleep(0.5)

            if relay_config['status'][relay] == '1':
                relay_object.start()

            elif relay_config['status'][relay] == '0':
                relay_object.stop()

            else:
                log.error('Wrong status on ini file must be 1 or 0')
                sys.exit(1)

    schedules = db.query(Schedules).all()
    for schedule in schedules:
        print ('Adding schedule with ID: {0} for relay {1}'.format(schedule.id, schedule.relay))
        cron_schedule = scheduler.Cron(schedule.id)
        cron_schedule.add_schedule(schedule.relay, schedule.start_time, schedule.stop_time)

    try:
        while True:
            total = 0

            for x in range(0, 9):
                total += rc_time(pimat_config['pins']['ldr_sensor'])

            average = total / 10

            try:
                light = (1 / float(average)) * 10000
            except ZeroDivisionError:
                light = 10000

            if light > 10000:
                light = 10000

            humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, pimat_config['pins']['temp_sensor'])

            if humidity is not None and temperature is not None and light is not None:
                log.info('Temp={0:0.1f}* Humidity={1:0.1f}% Light={2:0.2f}'.format(temperature, humidity, light))
                reading = Sensors(temperature, humidity, light)
                db.add(reading)
                db.commit()

            else:
                log.error('Failed to get reading. Try again!')
                GPIO.cleanup()
                scheduler.remove_all()
                db.close()

                raise Exception('Failed to get reading')

            time.sleep(120)

    except KeyboardInterrupt:
        print('Program received a Ctrl+C signal')
    finally:
        GPIO.cleanup()
        scheduler.remove_all()
        db.close()

signal.signal(signal.SIGTERM, sigterm_handler)

if __name__ == '__main__':
    main()
