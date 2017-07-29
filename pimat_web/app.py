#!/usr/bin/python
import configparser
from flask import Flask, request, redirect
from flask import render_template
from flask import url_for
import signal
import sys
from pimat_server.relays import get_pin_status, Relays
from flaskext.mysql import MySQL
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from pimat_server.scheduler import add_schedule

relay_config = configparser.ConfigParser()
relay_config.read('/opt/pimat/relays.ini')


app = Flask(__name__)
mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'zaq12wsx'
app.config['MYSQL_DATABASE_DB'] = 'pimat'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:zaq12wsx@localhost/pimat'
app.config['SQLALCHEMY_ECHO'] = False

db = SQLAlchemy(app)


def sigterm_handler(_signo, _stack_frame):
    # When sysvinit sends the TERM signal, cleanup before exiting.
    print("received signal {}, exiting...".format(_signo))
    sys.exit(0)


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
    start_time = db.Column(db.Time)
    stop_time = db.Column(db.Time)
    enabled = db.Column(db.String(1))

    def __init__(self, relay, switch, start_time, stop_time, enabled):
        self.relay = relay
        self.switch = switch
        self.start_time = start_time
        self.stop_time = stop_time
        self.enabled = enabled


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

    return render_template('index.html',
                           pins=relay_pins,
                           status=relay_status,
                           sensors_data=Sensors.query.order_by(Sensors.timestamp.asc()).all(),
                           schedules=Schedules.query.order_by(Schedules.relay.asc()).all()
                           )


@app.route("/schedule/add", methods=['POST', 'GET'])
def add_new_schedule():
    if request.method == 'POST':
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

        schedule = Schedules(relay, switch, start_time, stop_time, '1')
        db.session.add(schedule)
        db.session.commit()

        last = Schedules.query.order_by(Schedules.id.desc()).first()
        print last.id
        add_schedule(relay, start_time, stop_time)

        return redirect('/')

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


@app.route("/sensors", methods=['GET'])
def sensors():
    if request.args.get('sensor') and request.args.get('dates'):
        sensor = request.form.get("sensor")
        dates = request.form.get("start_date")

        print (dates)
        print (sensor)

        result = Sensors.query.filter_by(Sensors.timestamp.between('2017-07-28', '2017-07-29'))
        print result


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

