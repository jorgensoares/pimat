#!/usr/bin/python
import configparser
from flask import Flask, request, redirect, render_template, flash, url_for
from flask_restful import Api, Resource, reqparse
import signal
import sys
from pimat_server.relays import get_pin_status, Relays
from flask_sqlalchemy import SQLAlchemy
from pimat_server.scheduler import Cron
from datetime import datetime, timedelta
from flask_login import *
import logging
import json
from version import __version__
version = __version__

relay_config = configparser.ConfigParser()
relay_config.read('/opt/pimat/relays.ini')
file_handler = logging.FileHandler('/var/log/pimat-web.log')

app = Flask(__name__)
api = Api(app)
app.secret_key = 'super secret string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:zaq12wsx@localhost/pimat'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

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

def to_json(inst, cls):
    """
    Jsonify the sql alchemy query result.
    """
    convert = dict()
    # add your coversions for things like datetime's
    # and what-not that aren't serializable.
    d = dict()
    for c in cls.__table__.columns:
        v = getattr(inst, c.name)
        if c.type in convert.keys() and v is not None:
            try:
                d[c.name] = convert[c.type](v)
            except:
                d[c.name] = "Error:  Failed to covert using ", str(convert[c.type])
        elif v is None:
            d[c.name] = str()
        else:
            d[c.name] = v
    return json.dumps(d)


class SensorsAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('timestamp', type=str, required=True, location='json')
        self.reqparse.add_argument('temperature1', type=float, default="", location='json')
        self.reqparse.add_argument('temperature2', type=float, default="", location='json')
        self.reqparse.add_argument('humidity', type=float, default="", location='json')
        self.reqparse.add_argument('light1', type=float, default="", location='json')
        self.reqparse.add_argument('pressure', type=float, default="", location='json')
        self.reqparse.add_argument('altitude', type=float, default="", location='json')
        self.reqparse.add_argument('source', type=str, required=True, location='json')
        super(SensorsAPI, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        reading = Sensors(args['timestamp'], args['temperature1'], args['humidity'], args['light1'], args['source'])
        db.session.add(reading)
        db.session.commit()
        print args
        return {'Status': 'success'}, 201


class SchedulesAPI(Resource):

    def get(self):
        schedules = Schedules.query.order_by(Schedules.relay.asc()).all()
        return Schedules.query.order_by(Schedules.relay.asc()).all(), 201


class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(64))
    email = db.Column(db.String(120))

    def __init__(self, first_name, last_name, username, password, email):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = password
        self.email = email

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

    def __init__(self, timestamp,temperature1, humidity, light1, source):
        self.timestamp = timestamp
        self.temperature1 = temperature1
        self.humidity = humidity
        self.light1 = light1
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

    @property
    def json(self):
        return to_json(self, self.__class__)


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)


@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'


@app.route("/")
def index():
    if current_user.is_authenticated:
        app.logger.info('informing')
        app.logger.warning('warning')
        app.logger.error('screaming bloody murder!')
        return redirect(url_for("dashboard"))

    else:
        return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get("username")).first()

        if user:
            if user.password == request.form.get("password"):
                login_user(user, remember=True)
                flash('Welcome {0} {1}'.format(user.first_name, user.last_name))

                return redirect(url_for("index"))
    else:
        return render_template("login.html")


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    relay_status = dict()
    relay_status['relay1'] = get_pin_status(relay_config['pins']['relay1'])
    relay_status['relay2'] = get_pin_status(relay_config['pins']['relay2'])
    relay_status['relay3'] = get_pin_status(relay_config['pins']['relay3'])
    relay_status['relay4'] = get_pin_status(relay_config['pins']['relay4'])

    sensors_data = Sensors.query.filter(Sensors.timestamp.between(get_previous_date(1), get_now())).\
        order_by(Sensors.timestamp.asc()).all()

    return render_template('index.html',
                           version=version,
                           relay_config=relay_config,
                           status=relay_status,
                           sensors_data=sensors_data,
                           schedules=Schedules.query.order_by(Schedules.relay.asc()).all(),
                           last_reading=Sensors.query.order_by(Sensors.timestamp.desc()).first()
                           )


@app.route("/schedule/<action>/<schedule_id>", methods=['POST', 'GET'])
@login_required
def add_new_schedule(action, schedule_id):
    if request.method == 'POST' and action == 'add':
        relay = request.form.get("relay")
        start_time = request.form.get("start_time")
        stop_time = request.form.get("stop_time")

        if start_time >= stop_time:
            flash('The stop time cannot be equal or smaller than the start time, please try again!')
            return render_template('schedules.html', version=version, schedule=None)

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

        schedule = Schedules(relay, switch, start_time, stop_time, 'enable')
        db.session.add(schedule)
        db.session.commit()

        last = Schedules.query.order_by(Schedules.id.desc()).first()
        cron_schedule = Cron(last.id)
        cron_schedule.add_schedule(relay, start_time, stop_time)

        return redirect(url_for("dashboard"))

    elif request.method == 'POST' and action == 'delete':
        cron_schedule = Cron(schedule_id)
        cron_schedule.remove_schedule()
        Schedules.query.filter(Schedules.id == schedule_id).delete()
        db.session.commit()

        return url_for('dashboard')

    elif request.method == 'POST' and action == 'switch':
        cron_schedule = Cron(schedule_id)
        schedule = Schedules.query.filter(Schedules.id == schedule_id).first()

        if schedule.enabled == 'enable':
            cron_schedule.disable_schedule()
            schedule.enabled = 'disable'
            db.session.commit()

        else:
            cron_schedule.enable_schedule()
            schedule.enabled = 'enable'
            db.session.commit()

        return url_for('dashboard')

    elif request.method == 'POST' and action == 'edit':
        cron_schedule = Cron(schedule_id)
        schedule = Schedules.query.filter(Schedules.id == schedule_id).first()

        if request.form.get("start_time") >= request.form.get("stop_time"):
            flash('The stop time cannot be equal or smaller than the start time, please try again!')
            return render_template('schedules.html', version=version, schedule=None)

        schedule.start_time = request.form.get("start_time")
        schedule.stop_time = request.form.get("stop_time")
        db.session.commit()
        cron_schedule.edit(request.form.get("start_time"), request.form.get("stop_time"))

        return redirect(url_for("dashboard"))

    elif request.method == 'GET' and action == 'edit':
        schedule = Schedules.query.filter(Schedules.id == schedule_id).first()
        return render_template('schedules.html', version=version, schedule=schedule)

    else:
        return render_template('schedules.html', version=version, schedule=None)


@app.route("/relays/<action>/<relay>", methods=['POST'])
@login_required
def switch_relay(action, relay):
    if action and relay:

        pin = relay_config['pins'][relay]

        if action == 'on':
            relay_object = Relays(relay, pin)
            relay_object.start()
            return url_for('dashboard')

        elif action == 'off':
            relay_object = Relays(relay, pin)
            relay_object.stop()
            return url_for('dashboard')

        else:
            return render_template('error.html', error="Relay must be ON or OFF")
    else:
        return render_template('error.html', error="wrong request")


@app.route("/sensors", methods=['POST', 'GET'])
@login_required
def sensors():
    if request.args.get('sensor') and request.args.get('dates'):

        sensor = request.args.get("sensor")
        start_date, end_date = request.args.get("dates").split(' - ')
        end_date = '{0} 23:59:59'.format(end_date)
        sensor_column = 'sensors.%s' % sensor

        result = Sensors.query.with_entities(Sensors.timestamp, sensor_column).\
            filter(Sensors.timestamp.between(start_date, end_date)).all()

        return render_template('sensors.html',
                               version=version,
                               result=result,
                               sensor=sensor,
                               dates=request.args.get("dates"))

    else:
        return render_template('sensors.html', version=version)


@app.route("/camera", methods=['GET'])
@login_required
def camera():
    return render_template('camera.html', version=version)


@app.route("/logs", methods=['GET'])
@login_required
def logs():
    with open("/var/log/pimat/pimat-server.log", "r") as f:
        pimat_server_log = f.read()

    with open("/var/log/pimat/pimat-web.log", "r") as f:
        pimat_web_log = f.read()

    return render_template('logs.html',
                           version=version,
                           pimat_server_log=pimat_server_log,
                           pimat_web_log=pimat_web_log
                           )


@app.route("/profile", methods=['GET'])
@login_required
def profile():
    return render_template('profile.html', version=version)


@app.route("/user/create", methods=['GET'])
@login_required
def edit_user(action,user_id):
    return render_template('create_user.html', version=version)


@app.route("/users", methods=['GET'])
@login_required
def users():
    return render_template('users.html',
                           version=version,
                           users=User.query.order_by(User.id.asc()).all()
                           )


@app.errorhandler(404)
def not_found(error):
    return render_template('404', error=error)


api.add_resource(SensorsAPI, '/api/sensors')
api.add_resource(SchedulesAPI, '/api/schedules')


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)

    app.run(host='0.0.0.0',
            port=80,
            debug=True)


if __name__ == "__main__":
    main()

