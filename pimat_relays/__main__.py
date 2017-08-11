#!/usr/bin/python
import configparser
from subprocess import call, check_output
import sys
import datetime
import json
import requests

pimat_api_endpoint = 'http://localhost/api/v1/relay/logger'

relay_file = '/opt/pimat/relays.ini'
relay_config = configparser.ConfigParser()
relay_config.read(relay_file)

def get_now():
    # get the current date and time as a string
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


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


def get_pin_status(pin):
    status = check_output(['gpio', 'read', pin])

    if status[0] == '0':
        return 'ON'

    elif status[0] == '1':
        return 'OFF'

    else:
        return None


class Relays(object):
    def __init__(self, relay, pin):
        self.relay = relay
        self.pin = pin


    def start(self):
        call(['gpio', 'mode', self.pin, 'out'])
        call(['gpio', 'write', self.pin, '0'])
        relay_config.set('status', self.relay, '1')

        with open(relay_file, 'w') as ini_file:
            relay_config.write(ini_file)

        json_data = dict()
        json_data['timestamp'] = get_now()
        json_data['relay'] = self.relay
        json_data['pin'] = self.pin
        json_data['action'] = 'start'
        json_data['value'] = '1'
        json_data['source'] = 'pimat-client-1'

        requests.post(pimat_api_endpoint, data=json.dumps(json_data, default=json_serial),
                                 headers={'content-type': 'application/json'})

        return 'started'

    def stop(self):
        call(['gpio', 'mode', self.pin, 'out'])
        call(['gpio', 'write', self.pin, '1'])
        relay_config.set('status', self.relay, '0')

        with open(relay_file, 'w') as ini_file:
            relay_config.write(ini_file)

        json_data = dict()
        json_data['timestamp'] = get_now()
        json_data['relay'] = self.relay
        json_data['pin'] = self.pin
        json_data['action'] = 'stop'
        json_data['value'] = '0'
        json_data['source'] = 'pimat-client-1'

        requests.post(pimat_api_endpoint, data=json.dumps(json_data, default=json_serial),
                                 headers={'content-type': 'application/json'})

        return 'stopped'

    def set_mode(self, mode='out'):
        call(['gpio', 'mode', self.pin, mode])

        json_data = dict()
        json_data['timestamp'] = get_now()
        json_data['relay'] = self.relay
        json_data['pin'] = self.pin
        json_data['action'] = 'mode'
        json_data['value'] = mode
        json_data['source'] = 'pimat-client-1'

        requests.post(pimat_api_endpoint, data=json.dumps(json_data, default=json_serial),
                                 headers={'content-type': 'application/json'})
        return mode


def main():
    action = sys.argv[1]
    relay = sys.argv[2]
    relay_list = []

    for each in relay_config['pins']:
        relay_list.append(each)

    print action

    if relay in relay_list:
        pin = relay_config['pins'][relay]
        relay_object = Relays(relay, pin)

        if action == 'start':
            relay_object.set_mode()
            relay_object.start()

        elif action == 'stop':
            relay_object.set_mode()
            relay_object.stop()

        else:
            print('Wrong command line args use stop or start')
            sys.exit(1)

    else:
        print('Relay ID does not exist must be between 1 and 4')
        sys.exit(1)

if __name__ == '__main__':
    main()
