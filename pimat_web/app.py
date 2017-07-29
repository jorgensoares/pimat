#!/usr/bin/python
import configparser
from flask import Flask, request, redirect
from flask import render_template
from flask import url_for
import signal
import sys
from pimat_server.relays import get_pin_status, Relays
from flask_sqlalchemy import SQLAlchemy
from pimat_server.scheduler import add_schedule, remove_schedule
from datetime import datetime, timedelta
from flask_login import *

relay_config = configparser.ConfigParser()
relay_config.read('/opt/pimat/relays.ini')

app = Flask(__name__)
app.secret_key = 'super secret string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:zaq12wsx@localhost/pimat'
app.config['SQLALCHEMY_ECHO'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


def get_previous_date(days):
    return datetime.today() - timedelta(days=days)


def get_now():
    # get the current date and time as a string
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def sigterm_handler(_signo, _stack_frame):
    # When sysvinit sends the TERM signal, cleanup before exiting.
    print("received signal {}, exiting...".format(_signo))
    sys.exit(0)


# Create user model.
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120))
    password = db.Column(db.String(64))

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.username


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

    def __init__(self, temperature1, humidity, light1):
        self.timestamp = datetime.now()
        self.temperature1 = temperature1
        self.humidity = humidity
        self.light1 = light1
        self.source = 'pimat_server'


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


@login_manager.user_loader
def user_loader(user_id):
    """Given *user_id*, return the associated User object.

    :param unicode user_id: user_id (email) user to retrieve
    """
    return User.query.get(user_id)


@app.route("/login", methods=["GET", "POST"])
def login():
    """For GET requests, display the login form. For POSTS, login the current user
    by processing the form."""

    user = User.query.get(request.form.get("username"))
    if user:
        if user.password == request.form.get("password"):
            login_user(user, remember=True)
            return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    """Logout the current user."""
    logout_user()
    return render_template("logout.html")


@app.route("/")
def index():
    relay_pins = dict()
    relay_status = dict()
    relay_pins['relay1'] = relay_config['pins']['relay1']
    relay_pins['relay2'] = relay_config['pins']['relay2']
    relay_pins['relay3'] = relay_config['pins']['relay3']
    relay_pins['relay4'] = relay_config['pins']['relay4']
    relay_status['relay1'] = get_pin_status(relay_pins['relay1'])
    relay_status['relay2'] = get_pin_status(relay_pins['relay2'])
    relay_status['relay3'] = get_pin_status(relay_pins['relay3'])
    relay_status['relay4'] = get_pin_status(relay_pins['relay4'])

    sensors_data = Sensors.query.filter(Sensors.timestamp.between(get_previous_date(1), get_now())).\
        order_by(Sensors.timestamp.asc()).all()

    last_reading = Sensors.query.order_by(Sensors.timestamp.desc()).first()

    return render_template('index.html',
                           pins=relay_pins,
                           status=relay_status,
                           sensors_data=sensors_data,
                           schedules=Schedules.query.order_by(Schedules.relay.asc()).all(),
                           last_reading=last_reading
                           )


@app.route("/schedule/<action>/<schedule_id>", methods=['POST', 'GET'])
def add_new_schedule(action, schedule_id):
    if request.method == 'POST' and action == 'add':
        relay = request.form.get("relay")
        start_time = request.form.get("start_time")
        stop_time = request.form.get("stop_time")

        if relay == 'relay1':
            switch = 'Lights Switch'
        elif relay == 'relay2':
            switch = 'Exhaust Switch'
        elif relay == 'relay3':
            switch = 'Fan Switch'
        elif relay == 'relay4':
            switch = 'Pump Switch'
        else:
            switch = None

        schedule = Schedules(relay, switch, start_time, stop_time, 'enabled')
        db.session.add(schedule)
        db.session.commit()

        last = Schedules.query.order_by(Schedules.id.desc()).first()
        add_schedule(relay, start_time, stop_time, last.id)

        return redirect('/')

    elif request.method == 'POST' and action == 'delete':
        remove_schedule(schedule_id)
        Schedules.query.filter(Schedules.id == schedule_id).delete()
        db.session.commit()

        return url_for('index')

    else:
        return render_template('schedules.html')


@app.route("/relays/<action>/<relay>", methods=['POST'])
def switch_relay(action, relay):
    if action and relay:

        pin = relay_config['pins'][relay]

        if action == 'on':
            relay_object = Relays(relay, pin)
            relay_object.start()
            return url_for('index')

        elif action == 'off':
            relay_object = Relays(relay, pin)
            relay_object.stop()
            return url_for('index')

        else:
            return render_template('error.html', error="Relay must be ON or OFF")
    else:
        return render_template('error.html', error="wrong request")

@login_required
@app.route("/sensors", methods=['POST', 'GET'])
def sensors():
    if request.args.get('sensor') and request.args.get('dates'):

        sensor = request.args.get("sensor")
        start_date, end_date = request.args.get("dates").split(' - ')
        end_date = '{0} 23:59:59'.format(end_date)
        sensor_column = 'sensors.%s' % sensor

        result = Sensors.query.with_entities(Sensors.timestamp, sensor_column).\
            filter(Sensors.timestamp.between(start_date, end_date)).all()

        return render_template('sensors.html', result=result, sensor=sensor, dates=request.args.get("dates"))

    else:
        return render_template('sensors.html')


@app.route("/camera", methods=['GET'])
def camera():
    return render_template('camera.html')


@app.route("/logs", methods=['GET'])
def logs():
    with open("/var/log/pimat/sensors.log", "r") as f:
        sensors_log = f.read()

    with open("/var/log/pimat/pimat-web.log", "r") as f:
        pimat_web_log = f.read()

    return render_template('logs.html', sensors_log=sensors_log, pimat_web_log=pimat_web_log)


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)

    app.run(host='0.0.0.0',
            port=80,
            debug=True)


if __name__ == "__main__":
    main()

