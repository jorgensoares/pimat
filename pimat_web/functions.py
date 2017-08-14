from datetime import datetime, timedelta
import sys

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def get_previous_date(days):
    return datetime.today() - timedelta(days=days)


def get_now():
    # get the current date and time as a string
    return datetime.now()


def sigterm_handler(_signo, _stack_frame):
    # When sysvinit sends the TERM signal, cleanup before exiting.
    print("received signal {}, exiting...".format(_signo))
    sys.exit(0)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def convert_bytes(size):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    if size == 0:
        size = '0 B'
        return size
    i = 0
    while size >= 1024 and i < len(suffixes) - 1:
        size /= 1024.
        i += 1
    f = ('%.2f' % size).rstrip('0').rstrip('.')

    return '{0} {1}'.format(f, suffixes[i])


def convert_timestamp(timestamp):
    boot_time = datetime.utcfromtimestamp(timestamp)
    seconds = (boot_time - datetime.utcnow()).total_seconds()
    sec = timedelta(seconds=int(seconds))
    d = datetime(1, 1, 1) + sec

    return "%d days,  %d hours,  %d min,  %d sec" % (d.day - 1, d.hour, d.minute, d.second)
