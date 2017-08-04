#!/usr/bin/python
from flask import Flask, abort
from flask_restful import Api, Resource, reqparse
import datetime
from cron import Cron, remove_all
import logging
import sys
import requests
import json
import signal


app = Flask(__name__)
api = Api(app)


def sigterm_handler(_signo, _stack_frame):
    # When sysvinit sends the TERM signal, cleanup before exiting.
    print("[" + get_now() + "] received signal {}, exiting...".format(_signo))
    remove_all()
    sys.exit(0)


def get_now():
    # get the current date and time as a string
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def boot_sequence():
    # Clean cron
    remove_all()

    server_log = logging.getLogger()
    handler = logging.FileHandler('/var/log/pimat/pimat-server.log')
    formatter = logging.Formatter('[%(levelname)s] [%(asctime)-15s] [PID: %(process)d] [%(name)s] %(message)s')
    handler.setFormatter(formatter)
    server_log.addHandler(handler)
    server_log.setLevel(logging.DEBUG)

    retries = 4
    while retries > 1:
        retries -= 1
        get_schedules = requests.get("http://localhost/api/schedules")

        if get_schedules.status_code == 200:
            server_log.info('Schedules received!')
            break

    schedules = json.loads(get_schedules.content)

    for schedule in schedules['schedules']:
        server_log.info('Adding schedule with ID: {0} for {1}'.format(schedule['id'], schedule['relay']))
        cron_schedule = Cron(schedule['id'])
        cron_schedule.add_schedule(schedule['relay'], schedule['start_time'], schedule['stop_time'])


class ScheduleAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('relay', type=str, default="", location='json')
        self.reqparse.add_argument('start_time', type=str, default="", location='json')
        self.reqparse.add_argument('stop_time', type=str, default="", location='json')
        self.reqparse.add_argument('action', type=str, default="", location='json')
        super(ScheduleAPI, self).__init__()

    def put(self, id):
        args = self.reqparse.parse_args()

        if args.action == 'disable':
            cron_object = Cron(id)
            cron_object.disable_schedule()
            return {'status': 'success'}, 200

        elif args.action == 'enable':
            cron_object = Cron(id)
            cron_object.enable_schedule()
            return {'status': 'success'}, 200

        elif args.action == 'edit':
            if len(args.start_time) == 0 or len(args.stop_time) == 0:
                abort(404)

            cron_object = Cron(id)
            cron_object.edit(args.start_time, args.stop_time)
            return {'status': 'success'}, 200

        else:
            return {'status': 'not a valid action'}, 404

    def post(self, id):
        args = self.reqparse.parse_args()
        if len(args.start_time) == 0 or len(args.stop_time) == 0:
            abort(404)

        cron_object = Cron(id)
        cron_object.add_schedule(args.relay, args.start_time, args.stop_time)
        return {'status': 'success'}, 201

    def delete(self, id):
        cron_object = Cron(id)
        cron_object.remove_schedule()
        return {'status': 'success'}, 200

    def get(self, id):
        cron_object = Cron(id)
        status = cron_object.check_status()
        return {'status': status}, 200


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)
    boot_sequence()
    app.run(host='0.0.0.0',
            port=4002,
            debug=True,
            use_reloader=False
            )

    remove_all()

api.add_resource(ScheduleAPI, '/schedules/<id>')

if __name__ == '__main__':
    main()
