#!/usr/bin/python
import datetime
import logging
import signal
import sys
import time

import Adafruit_DHT
import RPi.GPIO as GPIO
import configparser
from scheduler import add_schedule, remove_all
from relays import Relays

GPIO.setmode(GPIO.BCM)

# define the pin that goes to the circuit
pin_to_circuit = 27
dht_pin = 17


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


def get_now():
    # get the current date and time as a string
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def sigterm_handler(_signo, _stack_frame):
    # When sysvinit sends the TERM signal, cleanup before exiting.
    print("[" + get_now() + "] received signal {}, exiting...".format(_signo))
    GPIO.cleanup()
    remove_all()
    sys.exit(0)


signal.signal(signal.SIGTERM, sigterm_handler)


def main():
    relay_config = configparser.ConfigParser()
    relay_config.read('/opt/pimat/relays.ini')
    log = logging.getLogger()
    handler = logging.FileHandler('/opt/pimat/sensors.log')
    formatter = logging.Formatter('[%(levelname)s] [%(asctime)-15s] [PID: %(process)d] [%(name)s] %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    # Clean cron
    remove_all()

    for relay in relay_config['pins']:
        for pin in relay_config['pins'][relay]:

            relay_object = Relays(relay, pin)
            relay_object.set_mode()
            time.sleep(1)

            if relay_config['status'][relay] == '1':
                relay_object.start()

            elif relay_config['status'][relay] == '0':
                relay_object.stop()

            else:
                log.error('Wrong status on ini file must be 1 or 0')
                sys.exit(1)

    for relay in relay_config['schedules']:
        schedule = relay_config['schedules'][relay]
        start_time, stop_time = schedule.slipt('-')
        add_schedule(relay, start_time, stop_time)

    try:
        while True:
            total = 0
            for x in range(0, 9):
                total += rc_time(pin_to_circuit)

            average = total/10

            light = (1/float(average)) * 10000

            humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302, dht_pin)

            if humidity is not None and temperature is not None and light is not None:
                log.info('Temp={0:0.1f}* Humidity={1:0.1f}% Light={2:0.2f}'.format(temperature, humidity, light))

            else:
                log.error('Failed to get reading. Try again!')
                GPIO.cleanup()
                remove_all()
                raise Exception('Failed to get reading')

            time.sleep(120)

    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
        remove_all()


if __name__ == '__main__':
    main()