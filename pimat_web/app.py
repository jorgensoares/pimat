#!/usr/bin/python
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, redirect, render_template, flash, url_for
from flask_restful import Api, Resource, reqparse, marshal
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from version import __version__
from flask_restful import fields
from flask_login import *
import configparser
import logging
import signal
import sys
import requests
import json

version = __version__

relay_config = configparser.ConfigParser()
relay_config.read('/opt/pimat/relays.ini')
pimat_config = configparser.ConfigParser()
pimat_config.read('/opt/pimat/config.ini')

file_handler = logging.FileHandler('/var/log/pimat-web.log')

app = Flask(__name__)
api = Api(app)
mail = Mail(app)
app.secret_key = 'super secret string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:zaq12wsx@localhost/pimat'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)

app.config.update(
    #EMAIL SETTINGS
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME='you@google.com',
    MAIL_PASSWORD='GooglePasswordHere'
    )

schedules_fields = {
    'start_time': fields.String,
    'stop_time': fields.String,
    'relay': fields.String,
    'id': fields.String
}


def get_previous_date(days):
    return datetime.today() - timedelta(days=days)


def get_now():
    # get the current date and time as a string
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def sigterm_handler(_signo, _stack_frame):
    # When sysvinit sends the TERM signal, cleanup before exiting.
    print("received signal {}, exiting...".format(_signo))
    sys.exit(0)


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
        reading = Sensors(args['timestamp'], args['temperature1'], args['temperature2'], args['humidity'],
                          args['light1'], args['pressure'], args['altitude'], args['source'])
        db.session.add(reading)
        db.session.commit()
        return {'status': 'success'}, 201


class SchedulesAPI(Resource):

    def get(self):
        schedules = Schedules.query.order_by(Schedules.relay.asc()).all()
        return {'schedules': [marshal(schedule, schedules_fields) for schedule in schedules]}, 200


class RelayLoggerAPI(Resource):

    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('timestamp', type=str, required=True, location='json')
        self.reqparse.add_argument('relay', type=str, required=True, default="", location='json')
        self.reqparse.add_argument('pin', type=int, required=True, default="", location='json')
        self.reqparse.add_argument('action', type=str, required=True, default="", location='json')
        self.reqparse.add_argument('value', type=str, required=True, default="", location='json')
        self.reqparse.add_argument('type', type=str, default="", location='json')
        self.reqparse.add_argument('source', type=str, required=True, default="", location='json')
        super(RelayLoggerAPI, self).__init__()

    def post(self):
        args = self.reqparse.parse_args()
        action = RelayLogger(args['timestamp'], args['relay'], args['pin'], args['action'], args['value'], args['type'],
                              args['source'])
        db.session.add(action)
        db.session.commit()

        return {'status': 'success'}, 201


class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(255))
    email = db.Column(db.String(120))

    def __init__(self, first_name, last_name, username, password, email):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = password
        self.email = email

    def generate_auth_token(self, expiration=600):
        s = Serializer(app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps({'username': self.username})

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = User.query.get(data['username'])
        return user

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

    def __init__(self, timestamp, temperature1, temperature2, humidity, light1, pressure, altitude,  source):
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


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for("login"))


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    else:
        return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == 'POST' and request.form.get("username") and request.form.get("password"):
        user = User.query.filter_by(username=request.form.get("username")).first()
        if user:
            if check_password_hash(user.password, request.form.get("password")):
                login_user(user, remember=True)
                flash('Welcome {0} {1}'.format(user.first_name, user.last_name), 'success')

                return redirect(url_for("index"))

            else:
                flash('Wrong Password', 'danger')
                return render_template("login.html")
        else:
            flash('User not found!', 'warning')
            return render_template("login.html")

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

    try:
        response = requests.get('http://localhost:4001/api/relay/{0}'.format(relay_config['pins']['relay1']),
                                timeout=0.5)
        status = json.loads(response.content)
        relay_status['relay1'] = status['status']

    except requests.ConnectionError:
        relay_status['relay1'] = 'N/A'

    try:
        response = requests.get('http://localhost:4001/api/relay/{0}'.format(relay_config['pins']['relay2']),
                                timeout=0.5)
        status = json.loads(response.content)
        relay_status['relay2'] = status['status']

    except requests.ConnectionError:
        relay_status['relay2'] = 'N/A'

    try:
        response = requests.get('http://localhost:4001/api/relay/{0}'.format(relay_config['pins']['relay3']),
                                timeout=0.5)
        status = json.loads(response.content)
        relay_status['relay3'] = status['status']

    except requests.ConnectionError:
        relay_status['relay3'] = 'N/A'

    try:
        response = requests.get('http://localhost:4001/api/relay/{0}'.format(relay_config['pins']['relay4']),
                                timeout=0.5)
        status = json.loads(response.content)
        relay_status['relay4'] = status['status']

    except requests.ConnectionError:
        relay_status['relay4'] = 'N/A'

    sensors_data = Sensors.query.filter(Sensors.timestamp.between(get_previous_date(1), get_now())).\
        order_by(Sensors.timestamp.asc()).all()

    relay_log = RelayLogger.query.filter(RelayLogger.timestamp.between(get_previous_date(1), get_now())).\
        order_by(RelayLogger.timestamp.asc()).all()

    return render_template('index.html',
                           version=version,
                           relay_config=relay_config,
                           status=relay_status,
                           sensors_data=sensors_data,
                           schedules=Schedules.query.order_by(Schedules.relay.asc()).all(),
                           last_reading=Sensors.query.order_by(Sensors.timestamp.desc()).first(),
                           relay_log=relay_log
                           )


@app.route("/schedule/<action>/<schedule_id>", methods=['POST', 'GET'])
@login_required
def add_new_schedule(action, schedule_id):
    if request.method == 'POST' and action == 'add':
        relay = request.form.get("relay")
        start_time = request.form.get("start_time")
        stop_time = request.form.get("stop_time")

        if start_time >= stop_time:
            flash('The stop time cannot be equal or smaller than the start time, please try again!', 'warning')
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

        json_data=dict()
        json_data['relay'] = relay
        json_data['start_time'] = str(start_time)
        json_data['stop_time'] = str(stop_time)

        response = requests.post('http://localhost:4001/api/schedules/{}'.format(last.id), data=json.dumps(json_data),
                                 headers={'content-type': 'application/json'}, timeout=2)

        if response.status_code == 201:
            return redirect(url_for("dashboard"))

        else:
            Schedules.query.filter(Schedules.id == last.id).delete()
            db.session.commit()
            return render_template('error.html', error="something went wrong with the request")

    elif request.method == 'POST' and action == 'delete':
        response = requests.delete('http://localhost:4001/api/schedules/{}'.format(schedule_id), timeout=2)

        if response.status_code == 200:
            Schedules.query.filter(Schedules.id == schedule_id).delete()
            db.session.commit()
            return url_for('dashboard')

        else:
            return 404

    elif request.method == 'POST' and action == 'switch':
        schedule = Schedules.query.filter(Schedules.id == schedule_id).first()
        json_data = dict()

        if schedule.enabled == 'enable':
            json_data['action'] = 'disable'
            response = requests.put('http://localhost:4001/api/schedules/{}'.format(schedule_id),
                                    data=json.dumps(json_data),
                                    headers={'content-type': 'application/json'},
                                    timeout=2
                                    )

            if response.status_code == 200:
                schedule.enabled = 'disable'
                db.session.commit()
            else:
                return 404

        else:
            json_data['action'] = 'enable'
            response = requests.put('http://localhost:4001/api/schedules/{}'.format(schedule_id),
                                    data=json.dumps(json_data),
                                    headers={'content-type': 'application/json'},
                                    timeout=2
                                    )

            if response.status_code == 200:
                schedule.enabled = 'enable'
                db.session.commit()
            else:
                return 404

        return url_for('dashboard')

    elif request.method == 'POST' and action == 'edit':
        schedule = Schedules.query.filter(Schedules.id == schedule_id).first()
        start_time = request.form.get("start_time")
        stop_time = request.form.get("stop_time")

        if request.form.get("start_time") >= request.form.get("stop_time"):
            flash('The stop time cannot be equal or smaller than the start time, please try again!', 'warning')
            return render_template('schedules.html', version=version, schedule=None)

        json_data = dict()
        json_data['action'] = 'edit'
        json_data['start_time'] = str(start_time)
        json_data['stop_time'] = str(stop_time)

        response = requests.put('http://localhost:4001/api/schedules/{}'.format(schedule_id),
                                data=json.dumps(json_data),
                                headers={'content-type': 'application/json'},
                                timeout=2
                                )

        if response.status_code == 200:
            schedule.start_time = start_time
            schedule.stop_time = stop_time
            db.session.commit()
            return redirect(url_for("dashboard"))
        else:
            return 404

    elif request.method == 'GET' and action == 'edit':
        schedule = Schedules.query.filter(Schedules.id == schedule_id).first()
        return render_template('schedules.html', version=version, schedule=schedule)

    else:
        return render_template('schedules.html', version=version, schedule=None)


@app.route("/relays/<action>/<relay>", methods=['POST'])
@login_required
def switch_relay(action, relay):
    if action and relay:
        json_data = dict()
        json_data['action'] = action
        json_data['relay'] = relay
        response = requests.put('http://localhost:4001/api/relay/{}'.format(relay_config['pins'][relay]),
                                data=json.dumps(json_data),
                                headers={'content-type': 'application/json'},
                                timeout=2
                                )

        if response.status_code == 200:
            return url_for('dashboard')
        else:
            return 404

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


@app.route("/monitoring", methods=['GET'])
@login_required
def monitoring():
    ip = pimat_config['pimat']['server_ip']
    return render_template('monitoring.html', ip=ip, version=version)


@app.route("/user/<action>/<user_id>", methods=['GET', 'POST'])
@login_required
def edit_user(action, user_id):
    if request.method == 'POST' and action == 'create':
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        verify_password = request.form.get("verify_password")

        if first_name and last_name and last_name and username and email and password and verify_password:
            if User.query.filter(User.username == username).all():
                flash('User already exists!', 'danger')
                return render_template('user_create.html', version=version)

            if password == verify_password:
                hashed_password = generate_password_hash(password)
                user = User(first_name, last_name, username, hashed_password, email)
                db.session.add(user)
                db.session.commit()

                return redirect(url_for("users"))

            else:
                flash('Passwords dont match, please try again!', 'danger')
                return render_template('user_create.html', version=version)

        else:
            flash('All fields are mandatory!', 'danger')
            return render_template('user_create.html', version=version)

    elif request.method == 'POST' and action == 'delete' and user_id:
        User.query.filter(User.id == user_id).delete()
        db.session.commit()

        return url_for("users")

    elif request.method == 'POST' and action == 'password_change':
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        verify_new_password = request.form.get("verify_new_password")

        if current_password and new_password and verify_new_password:
            if check_password_hash(current_user.password, current_password):
                if new_password == verify_new_password:
                    user = User.query.filter(User.id == current_user.id).first_or_404()
                    user.password = generate_password_hash(new_password)
                    db.session.commit()

                    flash('Password changed sucessfully, you should logout and login again!', 'success')
                    return redirect(url_for("dashboard"))

                else:
                    flash('Passwords dont Match!', 'danger')
                    return render_template('password_change.html', version=version)

            else:
                flash('Wrong Current Password', 'danger')
                return render_template('password_change.html', version=version)

        else:
            flash('All fields are mandatory!', 'danger')
            return render_template('password_change.html', version=version)

    else:
        return render_template('user_create.html', version=version)


@app.route("/users", methods=['GET'])
@login_required
def users():
    return render_template('users.html',
                           version=version,
                           users=User.query.order_by(User.id.asc()).all()
                           )


@app.route("/password_change", methods=['GET'])
@login_required
def password_change():
    return render_template('password_change.html', version=version)


@app.route("/reset_password", methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        user = request.form.get("username")

        if user:
            user_details = User.query.filter(User.username == user).first()
            s = Serializer(app.config['SECRET_KEY'], expires_in=600)
            token = s.dumps({'username': user_details.username})
            print user_details.email
            print token
                        
        else:
            return render_template('password_reset.html', version=version)

    return render_template('password_reset.html', version=version)


@app.errorhandler(404)
@login_required
def not_found(error):
    return render_template('error.html', error=error, version=version)


api.add_resource(SensorsAPI, '/api/sensors')
api.add_resource(SchedulesAPI, '/api/schedules')
api.add_resource(RelayLoggerAPI, '/api/v1/relay/logger')


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)
    db.create_all()
    app.run(host='0.0.0.0',
            port=80,
            threaded=True,
            debug=True,
            use_reloader=False
            )


if __name__ == "__main__":
    main()

