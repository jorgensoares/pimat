#!/usr/bin/env python
from subprocess import PIPE, Popen
import psutil
import os
import socket
import time

from datetime import datetime, timedelta

source = 'pimat-server'

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


def get_uname():
    process = Popen(['/bin/uname', '-srn'], stdout=PIPE)
    output, _error = process.communicate()
    return output.strip()


def main():
    status = dict()
    address = psutil.net_if_addrs()
    ram = psutil.virtual_memory()
    swap = psutil.swap_memory()
    disk = psutil.disk_usage('/')
    disk_boot = psutil.disk_usage('/boot')
    traffic = psutil.net_io_counters(pernic=True)
    load = os.getloadavg()

    status['timestamp'] = get_now()
    status['hostname'] = socket.gethostname()
    status['ip_eth0'] = address['eth0'][0].address
    status['ip_wlan0'] = ''
    status['timezone'] = time.tzname[time.daylight]
    status['boot_time'] = datetime.fromtimestamp(psutil.boot_time())
    status['cpu_temp'] = get_cpu_temperature()
    status['cpu_usage'] = psutil.cpu_percent(interval=1)
    status['cpu_frequency'] = psutil.cpu_freq()
    status['load_1'] = load[0]
    status['load_5'] = load[1]
    status['load_15'] = load[2]
    status['total_proc'] = len(psutil.pids())
    status['ram_total'] = ram.total
    status['ram_free'] = ram.free
    status['ram_used'] = ram.used
    status['ram_used_percent'] = ram.percent
    status['swap_total'] = swap.total
    status['swap_free'] = swap.free
    status['swap_used'] = swap.used
    status['swap_used_percent'] = swap.percent
    status['disk_total'] = disk.total
    status['disk_used'] = disk.used
    status['disk_free'] = disk.free
    status['disk_used_percent'] = disk.percent
    status['disk_total_boot'] = disk_boot.total
    status['disk_used_boot'] = disk_boot.used
    status['disk_free_boot'] = disk_boot.free
    status['disk_used_percent_boot'] = disk_boot.percent
    status['eth0_received'] = traffic['eth0'].bytes_recv
    status['eth0_sent'] = traffic['eth0'].bytes_sent
    status['wlan0_received'] = ''
    status['wlan0_sent'] = ''
    status['lo_received'] = traffic['lo'].bytes_recv
    status['lo_sent'] = traffic['lo'].bytes_sent
    status['kernel'] = get_uname()
    status['source'] = source
    


if __name__ == '__main__':
    main()