#!/usr/bin/python
from flask import Flask, abort
from flask_restful import Api, Resource, reqparse
import sys
import pimat_relays
import signal
import configparser
import logging
import time
import datetime


app = Flask(__name__)
api = Api(app)

relay_config = configparser.ConfigParser()
relay_config.read('/opt/pimat/relays.ini')
server_log = logging.getLogger()
handler = logging.FileHandler('/var/log/pimat/pimat-server.log')
formatter = logging.Formatter('[%(levelname)s] [%(asctime)-15s] [PID: %(process)d] [%(name)s] %(message)s')
handler.setFormatter(formatter)
server_log.addHandler(handler)
server_log.setLevel(logging.DEBUG)


def get_now():
    # get the current date and time as a string
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def sigterm_handler(_signo, _stack_frame):
    # When sysvinit sends the TERM signal, cleanup before exiting.
    print("[" + get_now() + "] received signal {}, exiting...".format(_signo))
    sys.exit(0)


def boot_sequence():
    server_log.info('Starting booting sequence at {0}'.format(get_now()))

    for relay in relay_config['pins']:
        for pin in relay_config['pins'][relay]:

            relay_object = pimat_relays.Relays(relay, pin)
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


class RelaysAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('relay', type=str, default="", location='json')
        self.reqparse.add_argument('action', type=str, default="", location='json')
        super(RelaysAPI, self).__init__()

    def put(self, pin):
        args = self.reqparse.parse_args()

        if args.action == 'on':
            relay_object = pimat_relays.Relays(args.relay, pin)
            relay_object.start()
            return {'status': 'success'}, 200

        if args.action == 'off':
            relay_object = pimat_relays.Relays(args.relay, pin)
            relay_object.stop()
            return {'status': 'success'}, 200

    def get(self, pin):
        status = pimat_relays.get_pin_status(pin)
        return {'status': status}, 200


api.add_resource(RelaysAPI, '/relay/<pin>')


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)
    app.run(host='0.0.0.0',
            port=4001,
            debug=True
            )


if __name__ == '__main__':
    main()
