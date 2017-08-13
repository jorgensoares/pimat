from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(255))
    email = db.Column(db.String(120))
    role = db.Column(db.String(10))
    phone = db.Column(db.String(16))
    email_alert = db.Column(db.String(3))
    sms_alert = db.Column(db.String(3))
    last_login = db.Column(db.DateTime)
    login_attempts = db.Column(db.String(2))

    def __init__(self, first_name, last_name, username, password, email, role='user', phone=None):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = password
        self.email = email
        self.role = role
        self.phone = phone

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

class Sensors(db.Model):
    __tablename__ = 'sensors'

    id = db.Column('id', db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    temperature1 = db.Column(db.Float)
    temperature2 = db.Column(db.Float)
    humidity = db.Column(db.Float)
    light1 = db.Column(db.Float)
    pressure = db.Column(db.Float)
    altitude = db.Column(db.Float)
    source = db.Column(db.String(100))

    def __init__(self, timestamp, temperature1, temperature2, humidity, light1, pressure, altitude, source):
        self.timestamp = timestamp
        self.temperature2 = temperature2
        self.temperature1 = temperature1
        self.humidity = humidity
        self.light1 = light1
        self.pressure = pressure
        self.altitude = altitude
        self.source = source


class Schedules(db.Model):
    __tablename__ = 'schedules'

    id = db.Column('id', db.Integer, primary_key=True)
    relay = db.Column(db.String(10))
    switch = db.Column(db.String(50))
    start_time = db.Column(db.String(5))
    stop_time = db.Column(db.String(5))
    enabled = db.Column(db.String(10))

    def __init__(self, relay, switch, start_time, stop_time, enabled):
        self.relay = relay
        self.switch = switch
        self.start_time = start_time
        self.stop_time = stop_time
        self.enabled = enabled


class RelayLogger(db.Model):
    __tablename__ = 'relay_logger'

    id = db.Column('id', db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    relay = db.Column(db.String(50))
    pin = db.Column(db.String(2))
    action = db.Column(db.String(10))
    value = db.Column(db.String(10))
    type = db.Column(db.String(20))
    source = db.Column(db.String(100))

    def __init__(self, timestamp, relay, pin, action, value, type, source):
        self.timestamp = timestamp
        self.relay = relay
        self.pin = pin
        self.action = action
        self.value = value
        self.type = type
        self.source = source


class Monitoring(db.Model):
    __tablename__ = 'monitoring'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime)
    hostname = db.Column(db.String(50), unique=True)
    ip_eth0 = db.Column(db.String(16))
    ip_wlan0 = db.Column(db.String(16))
    timezone = db.Column(db.String(5))
    boot_time = db.Column(db.Float)
    cpu_temp = db.Column(db.Float)
    cpu_usage = db.Column(db.Float)
    cpu_frequency = db.Column(db.Float)
    load_1 = db.Column(db.Float)
    load_5 = db.Column(db.Float)
    load_15 = db.Column(db.Float)
    total_proc = db.Column(db.Integer)
    ram_total = db.Column(db.Integer)
    ram_free = db.Column(db.Integer)
    ram_used = db.Column(db.Integer)
    ram_used_percent = db.Column(db.Float)
    swap_total = db.Column(db.Integer)
    swap_free = db.Column(db.Integer)
    swap_used = db.Column(db.Integer)
    swap_used_percent = db.Column(db.Float)
    disk_total = db.Column(db.Integer)
    disk_used = db.Column(db.Integer)
    disk_free = db.Column(db.Integer)
    disk_used_percent = db.Column(db.Float)
    disk_total_boot = db.Column(db.Integer)
    disk_used_boot = db.Column(db.Integer)
    disk_free_boot = db.Column(db.Integer)
    disk_used_percent_boot = db.Column(db.Float)
    eth0_received = db.Column(db.Integer)
    eth0_sent = db.Column(db.Integer)
    wlan0_received = db.Column(db.Integer)
    wlan0_sent = db.Column(db.Integer)
    lo_received = db.Column(db.Integer)
    lo_sent = db.Column(db.Integer)
    kernel = db.Column(db.String(50))
    source = db.Column(db.String(50))

    def __init__(self, timestamp, hostname, ip_eth0, ip_wlan0, timezone, boot_time, cpu_temp, cpu_usage, cpu_frequency,
                 load_1, load_5, load_15, total_proc, ram_total, ram_free, ram_used,ram_used_percent, swap_total,
                 swap_free, swap_used, swap_used_percent, disk_total, disk_used, disk_free, disk_used_percent,
                 disk_total_boot, disk_used_boot, disk_free_boot, disk_used_percent_boot, eth0_received, eth0_sent,
                 wlan0_received, wlan0_sent, lo_received, lo_sent, kernel, source):

        self.timestamp = timestamp
        self.hostname = hostname
        self.ip_eth0 = ip_eth0
        self.ip_wlan0 = ip_wlan0
        self.timezone = timezone
        self.boot_time = boot_time
        self.cpu_temp = cpu_temp
        self.cpu_usage = cpu_usage
        self.cpu_frequency = cpu_frequency
        self.load_1 = load_1
        self.load_5 = load_5
        self.load_15 = load_15
        self.total_proc = total_proc
        self.ram_total = ram_total
        self.ram_free = ram_free
        self.ram_used = ram_used
        self.ram_used_percent = ram_used_percent
        self.swap_total = swap_total
        self.swap_free = swap_free
        self.swap_used = swap_used
        self.swap_used_percent = swap_used_percent
        self.disk_total = disk_total
        self.disk_used = disk_used
        self.disk_free = disk_free
        self.disk_used_percent = disk_used_percent
        self.disk_total_boot = disk_total_boot
        self.disk_used_boot = disk_used_boot
        self.disk_free_boot = disk_free_boot
        self.disk_used_percent_boot = disk_used_percent_boot
        self.eth0_received = eth0_received
        self.eth0_sent = eth0_sent
        self.wlan0_received = wlan0_received
        self.wlan0_sent = wlan0_sent
        self.lo_received = lo_received
        self.lo_sent = lo_sent
        self.kernel = kernel
        self.source = source

