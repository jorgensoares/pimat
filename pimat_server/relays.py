#!/usr/bin/python
import configparser
from subprocess import call, check_output
import sys

relay_file = '/opt/pimat/relays.ini'
relay_config = configparser.ConfigParser()
relay_config.read(relay_file)


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
        call(['gpio', 'write', self.pin, '0'])
        print(self.relay)
        relay_config.set('status', self.relay, '1')

        with open(relay_file, 'w') as ini_file:
            relay_config.write(ini_file)

    def stop(self):
        call(['gpio', 'write', self.pin, '1'])
        print(self.relay)
        relay_config.set('status', self.relay, '0')

        with open(relay_file, 'w') as ini_file:
            relay_config.write(ini_file)

    def set_mode(self, mode='out'):
        call(['gpio', 'mode', self.pin, mode])
        print(mode)


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
