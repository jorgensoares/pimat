#!/usr/bin/env python
from subprocess import PIPE, Popen
import psutil
import os

from datetime import datetime, timedelta


def display_time(seconds):
    sec = timedelta(seconds=int(seconds))
    d = datetime(1,1,1) + sec

    return "%d days, %d hours, %d min, %d sec" % (d.day-1, d.hour, d.minute, d.second)

def get_now():
    # get the current date and time as a string
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')



def get_cpu_temperature():
    process = Popen(['/opt/vc/bin/vcgencmd', 'measure_temp'], stdout=PIPE)
    output, _error = process.communicate()
    return float(output[output.index('=') + 1:output.rindex("'")])


def main():
    cpu_temperature = get_cpu_temperature()
    cpu_usage = psutil.cpu_percent(interval=1)
    cpu_details = psutil.cpu_freq()
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    load = os.getloadavg()

    boot_time_seconds = (datetime.now()-boot_time).total_seconds()
    print 'Boot time: {0}'.format(display_time(boot_time_seconds))
    print 'Temp: {0}'.format(cpu_temperature)
    print 'CPU usage: {0}'.format(cpu_usage)
    print 'CPU frequency: {0}'.format(cpu_details.max)
    print 'Load 1min: {0}'.format(load[0])
    print 'Load 5min: {0}'.format(load[1])
    print 'Load 15min: {0}'.format(load[2])

    ram = psutil.virtual_memory()
    ram_total = ram.total / 2**20       # MiB.
    ram_used = ram.used / 2**20
    ram_free = ram.free / 2**20
    ram_percent_used = ram.percent

    print 'Total ram: {0}'.format(ram_total)
    print 'Ram USed: {0}'.format(ram_used)
    print 'Ram Free: {0}'.format(ram_free)
    print 'Ram Percent used: {0}'.format(ram_percent_used)

    disk = psutil.disk_usage('/')
    disk_total = disk.total / 2**30     # GiB.
    disk_used = disk.used / 2**30
    disk_free = disk.free / 2**30
    disk_percent_used = disk.percent

    print 'Total disk: {0}'.format(disk_total)
    print 'Disk Used: {0}'.format(disk_used)
    print 'Disk Free: {0}'.format(disk_free)
    print 'Disk percent used: {0}'.format(disk_percent_used)

    eth0 = psutil.net_io_counters(pernic=True)
    eth0_received = eth0['eth0'].bytes_recv
    eth0_sent = eth0['eth0'].bytes_sent

    print 'eth0_received: {0}'.format(eth0_received)
    print 'eth0_sent: {0}'.format(eth0_sent)


if __name__ == '__main__':
    main()