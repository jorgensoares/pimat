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
import requests
import json

GPIO.setmode(GPIO.BCM)


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""
    # yyyy-MM-dd'T'HH:mm:ss.SSS    strict_date_hour_minute_second_millis
    if isinstance(obj, datetime):
        tz_string = "Z"
        serial = "%s.%03d" % (
            obj.strftime("%Y-%m-%dT%H:%M:%S"),
            int(obj.microsecond / 1000))
        return serial
    raise TypeError("Type not serializable")


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
    retries = 3
    relay_config = configparser.ConfigParser()
    relay_config.read('/opt/pimat/relays.ini')
    pimat_config = configparser.ConfigParser()
    pimat_config.read('/opt/pimat/config.ini')

    server_log = logging.getLogger()
    handler = logging.FileHandler('/var/log/pimat/pimat-server.log')
    formatter = logging.Formatter('[%(levelname)s] [%(asctime)-15s] [PID: %(process)d] [%(name)s] %(message)s')
    handler.setFormatter(formatter)
    server_log.addHandler(handler)
    server_log.setLevel(logging.DEBUG)

    server_log.info('Starting booting sequence at {0}'.format(get_now()))

    # Clean cron
    scheduler.remove_all()

    for relay in relay_config['pins']:
        for pin in relay_config['pins'][relay]:

            relay_object = Relays(relay, pin)
            mode = relay_object.set_mode()
            server_log.info('Setting mode {0} for {1}'.format(mode, relay))
            time.sleep(0.5)

            if relay_config['status'][relay] == '1':
                status = relay_object.start()
                server_log.info('{0} was {1}'.format(relay, status))

            elif relay_config['status'][relay] == '0':
                status = relay_object.stop()
                server_log.info('{0} was {1}'.format(relay, status))

            else:
                server_log.error('Wrong status on ini file must be 1 or 0')
                raise Exception('Wrong status on ini file must be 1 or 0')

    while retries > 1:
        retries -= 1
        get_schedules = requests.get("http://localhost/api/schedules")

        if get_schedules.status_code == 200:
            server_log.info('Schedules received!')
            break

    schedules = json.loads(get_schedules.content)

    for schedule in schedules['schedules']:
        server_log.info('Adding schedule with ID: {0} for {1}'.format(schedule['id'], schedule['relay']))
        cron_schedule = scheduler.Cron(schedule['id'])
        cron_schedule.add_schedule(schedule['relay'], schedule['start_time'], schedule['stop_time'])

    try:
        server_log.info('Pimat server started, collecting sensors data.')

        while True:
            total = 0

            for x in range(0, 9):
                total += rc_time(int(pimat_config['pins']['ldr_sensor']))

            average = total / 10

            try:
                light = (1 / float(average)) * 10000
            except ZeroDivisionError:
                light = 10000

            if light > 10000:
                light = 10000

            humidity, temperature = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302,
                                                            int(pimat_config['pins']['temp_sensor']))

            if humidity is not None and temperature is not None and light is not None:
                json_data = dict()
                json_data['timestamp'] = get_now()
                json_data['temperature1'] = temperature
                json_data['humidity'] = humidity
                json_data['light1'] = light
                json_data['source'] = 'pimat_server'

                server_log.info('Temp={0:0.1f}* Humidity={1:0.1f}% Light={2:0.2f}'.format(temperature, humidity, light))

                while retries > 1:
                    retries -= 1
                    response = requests.post('http://localhost/api/sensors',
                                             data=json.dumps(json_data, default=json_serial),
                                             headers={'content-type': 'application/json'})

                    if response.status_code == 201:
                        server_log.info('Last reading was posted to http://10.14.11.252/api/sensors')
                        break

                    if response.status_code == 400:
                        server_log.error('bad request or wrong request data sent to server')
                        break

            else:
                server_log.error('Failed to get reading. Try again!')
                GPIO.cleanup()
                scheduler.remove_all()
                raise Exception('Failed to get reading')

            time.sleep(120)

    except KeyboardInterrupt:
        print('Program received a Ctrl+C signal')
    finally:
        GPIO.cleanup()
        scheduler.remove_all()

signal.signal(signal.SIGTERM, sigterm_handler)

if __name__ == '__main__':
    main()
