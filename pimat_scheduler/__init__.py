#!/usr/bin/python
import configparser
import datetime
from crontab import CronTab
import logging
import sys
import requests
import json

cron = CronTab(user='root')


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
                print job.command
                job.minute.on(minute)
                job.hour.on(hour)
                cron.write()

    def check_status(self):
        jobs = cron.find_comment(self.schedule_id)
        status = dict()
        n = 0

        for job in jobs:
            if job.is_enabled() is True:
                status["{0}".format(n)] = "enable"
                n += 1

            else:
                status["{0}".format(n)] = "disable"
                n += 1

        if status['1'] == status['0']:
            return 'enable'

        else:
            return 'disable'


def main():
    boot_sequence()


if __name__ == '__main__':
    main()
