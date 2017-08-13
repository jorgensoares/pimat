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