#!/usr/bin/python
import datetime
import logging
import signal
import sys
import time
import Adafruit_DHT
import RPi.GPIO as GPIO
import configparser
import pymysql as pymysql
import scheduler
from relays import Relays
from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base


# define the pin that goes to the circuit
GPIO.setmode(GPIO.BCM)
pin_to_circuit = 27
dht_pin = 17


# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base = declarative_base()


class Schedules(Base):

    __tablename__ = 'schedules'

    id = Column('id', Integer, primary_key=True)
    relay = Column(String(10))
    switch = Column(String(50))
    start_time = Column(String(5))
    stop_time = Column(String(5))
    enabled = Column(String(10))


engine = create_engine('mysql://root:zaq12wsx@localhost/pimat')
Base.metadata.bind = engine
Session = sessionmaker(bind=engine)
Session.configure(bind=engine)
db = Session()


def sigterm_handler(_signo, _stack_frame):
    # When sysvinit sends the TERM signal, cleanup before exiting.
    print("[" + get_now() + "] received signal {}, exiting...".format(_signo))
    GPIO.cleanup()
    scheduler.remove_all()
    sys.exit(0)


def get_now():
    # get the current date and time as a string
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

signal.signal(signal.SIGTERM, sigterm_handler)


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
    log = logging.getLogger()
    handler = logging.FileHandler('/var/log/pimat/sensors.log')
    formatter = logging.Formatter('[%(levelname)s] [%(asctime)-15s] [PID: %(process)d] [%(name)s] %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    db = pymysql.connect(host='localhost',
                         user='root',
                         password='zaq12wsx',
                         db='pimat',
                         charset='utf8mb4',
                         cursorclass=pymysql.cursors.DictCursor)

    # Clean stuff
    GPIO.cleanup()
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

    # with db.cursor() as cursor:
    #     cursor.execute('SELECT * FROM schedules;')
    #     schedules = cursor.fetchall()

    schedules = db.query(Schedules).all()

    for schedule in schedules:
        print(schedule)
        cron_schedule = scheduler.Cron(schedule['id'])
        cron_schedule.add_schedule(schedule['relay'], schedule['start_time'], schedule['stop_time'])

    try:
        while True:
            total = 0

            for x in range(0, 9):
                total += rc_time(pin_to_circuit)

            average = total / 10

            try:
                light = (1 / float(average)) * 10000
            except ZeroDivisionError:
                light = 10000

            if light > 10000:
                light = 10000

            humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, dht_pin)

            if humidity is not None and temperature is not None and light is not None:
                log.info('Temp={0:0.1f}* Humidity={1:0.1f}% Light={2:0.2f}'.format(temperature, humidity, light))

                with db.cursor() as cursor:
                    sql = """INSERT INTO `sensors` (`timestamp`, `temperature1`, `humidity`, `light1`, `source`)
                    VALUES (NOW(), %s, %s, %s, %s)"""
                    cursor.execute(sql, (temperature, humidity, light, 'pimat_server'))

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


if __name__ == '__main__':
    main()
