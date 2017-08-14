#!/usr/bin/python
import Adafruit_BMP.BMP085 as BMP085
from ldr import ldr_sensor
import RPi.GPIO as GPIO
import Adafruit_DHT
import configparser
import datetime
import requests
import logging
import signal
import time
import json
import sys

GPIO.setmode(GPIO.BCM)

relay_config = configparser.ConfigParser()
relay_config.read('/opt/pimat/relays.ini')
server_log = logging.getLogger()
handler = logging.FileHandler('/var/log/pimat/pimat-server.log')
formatter = logging.Formatter('[%(levelname)s] [%(asctime)-15s] [PID: %(process)d] [%(name)s] %(message)s')
handler.setFormatter(formatter)
server_log.addHandler(handler)
server_log.setLevel(logging.DEBUG)


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
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)
    pimat_config = configparser.ConfigParser()
    pimat_config.read('/opt/pimat/config.ini')
    bpm_sensor = BMP085.BMP085()

    try:
        while True:

            light = ldr_sensor(pimat_config['pins']['ldr_sensor'])
            humidity, temperature1 = Adafruit_DHT.read_retry(Adafruit_DHT.AM2302,
                                                            int(pimat_config['pins']['temp_sensor']))
            temperature2 = bpm_sensor.read_temperature()
            pressure = bpm_sensor.read_pressure()
            altitude = bpm_sensor.read_altitude()

            if humidity is not None and temperature1 is not None and light and temperature2 and pressure and altitude \
                    is not None:
                json_data = dict()
                json_data['timestamp'] = get_now()
                json_data['temperature1'] = temperature1
                json_data['temperature2'] = temperature2
                json_data['humidity'] = humidity
                json_data['light1'] = light
                json_data['pressure'] = pressure
                json_data['altitude'] = altitude
                json_data['source'] = 'pimat_server'

                server_log.info('''Temp1={0:0.1f}* Temp2={1:0.2f}* Humidity={2:0.1f}% Light={3:0.2f} Pressure={4:0.2f}Pa
                                    Altitude={5:0.2f}m'''.format(temperature1, temperature2, humidity, light, pressure,
                                                                 altitude))
                retries = 3
                while retries > 1:
                    retries -= 1
                    try:
                        response = requests.post('http://localhost/api/sensors',
                                                 data=json.dumps(json_data, default=json_serial),
                                                 headers={'content-type': 'application/json'})

                        if response.status_code == 201:
                            server_log.info('Last reading was posted to http://10.14.11.252/api/sensors')
                            break

                        if response.status_code == 400:
                            server_log.error('bad request or wrong request data sent to server')
                            break

                    except requests.ConnectionError:
                        server_log.debug('Could not connect to pimat web server')
                        time.sleep(2)

            else:
                server_log.error('Failed to get reading. Try again!')
                GPIO.cleanup()
                raise Exception('Failed to get reading')

            time.sleep(120)

    except KeyboardInterrupt:
        print('Program received a Ctrl+C signal')
    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    main()
