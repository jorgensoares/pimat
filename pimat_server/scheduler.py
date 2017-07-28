#!/usr/bin/python
from crontab import CronTab

cron = CronTab(user='root')


def add_schedule(relay, start_time, stop_time):
    start_hour, start_minute = start_time.split(':')
    start_job = cron.new(command='/usr/bin/python /opt/pimat/pimat_server/relays.py start %s' % relay,
                         comment='%s start' % relay)
    start_job.minute.on(start_minute)
    start_job.hour.on(start_hour)
    start_job.enable()

    stop_job = cron.new(command='/usr/bin/python /opt/pimat/pimat_server/relays.py stop %s' % relay,
                        comment='%s stop' % relay)
    stop_hour, stop_minute = stop_time.split(':')
    stop_job.minute.on(stop_minute)
    stop_job.hour.on(stop_hour)
    stop_job.enable()

    cron.write()


def remove_schedule(relay):
    cron.remove_all(command='%s' % relay)
    cron.write()


def remove_all():
    cron.remove_all(command='relay')




