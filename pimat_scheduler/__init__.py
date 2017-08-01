#!/usr/bin/python
import configparser
from flask import Flask, jsonify, abort, make_response
from flask_restful import Api, Resource, reqparse, fields, marshal
import datetime
from crontab import CronTab
import logging
import sys
import requests
import json
import signal

cron = CronTab(user='root')

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


def remove_all():
    cron.remove_all()
    cron.write()


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


class Cron(object):

    def __init__(self, schedule_id):
        self.schedule_id = schedule_id

    def add_schedule(self, relay, start_time, stop_time):
        start_hour, start_minute = start_time.split(':')
        start_job = cron.new(command='PATH=$PATH:/usr/local/bin /usr/local/bin/pimat-relay start %s' % relay,
                             comment='%s' % self.schedule_id)
        start_job.minute.on(start_minute)
        start_job.hour.on(start_hour)
        start_job.enable()

        stop_job = cron.new(command='PATH=$PATH:/usr/local/bin /usr/local/bin/pimat-relay stop %s' % relay,
                            comment='%s' % self.schedule_id)
        stop_hour, stop_minute = stop_time.split(':')
        stop_job.minute.on(stop_minute)
        stop_job.hour.on(stop_hour)
        stop_job.enable()

        cron.write()

    def remove_schedule(self):
        jobs = cron.find_comment(self.schedule_id)

        for job in jobs:
            cron.remove(job)
            cron.write()

    def disable_schedule(self):
        jobs = cron.find_comment(self.schedule_id)

        for job in jobs:
            job.enable(False)
            cron.write()

    def enable_schedule(self):
        jobs = cron.find_comment(self.schedule_id)

        for job in jobs:
            job.enable()
            cron.write()

    def edit(self, start_time, stop_time):
        jobs = cron.find_comment(self.schedule_id)

        for job in jobs:
            if 'start' in job.command:
                hour, minute = start_time.split(':')
                job.minute.on(minute)
                job.hour.on(hour)
                cron.write()
            else:
                hour, minute = stop_time.split(':')
                job.minute.on(minute)
                job.hour.on(hour)
                cron.write()

    def check_status(self):
        jobs = cron.find_comment(self.schedule_id)

        for job in jobs:
            if job:
                if job.is_enabled():
                    status = 'enable'
                else:
                    status = 'disable'

                return status

            else:
                return 'No jobs founds for the provided id'


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

        if args.action == 'enable':
            cron_object = Cron(id)
            cron_object.enable_schedule()
            return {'status': 'success'}, 200

        if args.action == 'edit':
            if len(args.start_time) == 0 or len(args.stop_time) == 0:
                abort(404)

            cron_object = Cron(id)
            cron_object.edit(args.start_time, args.stop_time)
            return {'status': 'success'}, 200

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

    def get(self, id):
        cron_object = Cron(id)
        status = cron_object.check_status()
        return {'status': status}, 200

api.add_resource(ScheduleAPI, '/schedules/<id>')


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)
    boot_sequence()
    app.run(host='0.0.0.0',
            port=4002,
            debug=True
            )

    remove_all()


if __name__ == '__main__':
    main()
