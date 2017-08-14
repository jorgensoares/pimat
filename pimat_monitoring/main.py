#!/usr/bin/env python
from subprocess import PIPE, Popen
import psutil
import os
import socket
import time
import logging
import json
import requests
from datetime import datetime

source = 'pimat-server'

server_log = logging.getLogger()
handler = logging.FileHandler('/var/log/pimat/pimat-server.log')
formatter = logging.Formatter('[%(levelname)s] [%(asctime)-15s] [PID: %(process)d] [%(name)s] %(message)s')
handler.setFormatter(formatter)
server_log.addHandler(handler)
server_log.setLevel(logging.DEBUG)


def get_now():
    # get the current date and time as a string
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_cpu_temperature():
    process = Popen(['/opt/vc/bin/vcgencmd', 'measure_temp'], stdout=PIPE)
    output, _error = process.communicate()
    return float(output[output.index('=') + 1:output.rindex("'")])


def get_uname():
    process = Popen(['/bin/uname', '-srn'], stdout=PIPE)
    output, _error = process.communicate()
    return output.strip()


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


def main():
    while True:
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
        status['boot_time'] = psutil.boot_time()
        status['cpu_temp'] = get_cpu_temperature()
        status['cpu_usage'] = psutil.cpu_percent(interval=1)
        status['cpu_frequency'] = psutil.cpu_freq()
        status['load_1'] = load[0]
        status['load_5'] = load[1]
        status['load_15'] = load[2]
        status['total_proc'] = len(psutil.pids())
        status['ram_total'] = str(ram.total)
        status['ram_free'] = str(ram.free)
        status['ram_used'] = str(ram.used)
        status['ram_used_percent'] = str(ram.percent)
        status['swap_total'] = str(swap.total)
        status['swap_free'] = str(swap.free)
        status['swap_used'] = str(swap.used)
        status['swap_used_percent'] = swap.percent
        status['disk_total'] = str(disk.total)
        status['disk_used'] = str(disk.used)
        status['disk_free'] = str(disk.free)
        status['disk_used_percent'] = disk.percent
        status['disk_total_boot'] = str(disk_boot.total)
        status['disk_used_boot'] = str(disk_boot.used)
        status['disk_free_boot'] = str(disk_boot.free)
        status['disk_used_percent_boot'] = disk_boot.percent
        status['eth0_received'] = str(traffic['eth0'].bytes_recv)
        status['eth0_sent'] = str(traffic['eth0'].bytes_sent)
        status['wlan0_received'] = '0'
        status['wlan0_sent'] = '0'
        status['lo_received'] = str(traffic['lo'].bytes_recv)
        status['lo_sent'] = str(traffic['lo'].bytes_sent)
        status['kernel'] = get_uname()
        status['source'] = source

        retries = 3
        while retries > 1:
            retries -= 1
            response = requests.post('http://localhost/api/v1/monitoring',
                                     data=json.dumps(status, default=json_serial),
                                     headers={'content-type': 'application/json'})

            if response.status_code == 201:
                server_log.info('Last reading was posted to http://10.14.11.252/api/sensors')
                print response.content
                break

            if response.status_code == 400:
                server_log.error('bad request or wrong request data sent to server')
                break

        time.sleep(30)


if __name__ == '__main__':
    main()
