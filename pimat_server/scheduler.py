#!/usr/bin/python
from crontab import CronTab

cron = CronTab(user='root')


def remove_all():
    cron.remove_all(command='pimat-relay')


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

