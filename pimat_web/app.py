#!/usr/bin/python
import configparser
from flask import Flask, request, redirect
from flask import render_template
from flask import url_for
import signal
import sys
from pimat_server.relays import get_pin_status, Relays
from flaskext.mysql import MySQL

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


def sigterm_handler(_signo, _stack_frame):
    # When sysvinit sends the TERM signal, cleanup before exiting.
    print("received signal {}, exiting...".format(_signo))
    sys.exit(0)


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

    timestamp = list()
    temperature1 = list()
    humidity = list()
    light1 = list()

    conn = mysql.connect()
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, temperature1, humidity, light1 from sensors where source='pimat_server'")

    for row in cursor.fetchall():
        timestamp.append(str(row[0]))
        temperature1.append(str(row[1]))
        humidity.append(str(row[2]))
        light1.append(str(row[3]))

    cursor.close()

    cursor = conn.cursor()
    cursor.execute("SELECT * from schedules")
    schedules = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('index.html',
                           pins=relay_pins,
                           status=relay_status,
                           timestamp=timestamp,
                           temperature1=temperature1,
                           humidity=humidity,
                           light1=light1,
                           schedules=schedules
                           )


@app.route("/schedule/add", methods=['POST', 'GET'])
def add_new_schedule():
    if request.method == 'POST':
        relay = request.form.get("relay")
        start_time = request.form.get("start_time")
        stop_time = request.form.get("stop_time")

        print(relay)
        print(start_time)
        print(stop_time)

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

        conn = mysql.connect()
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO `schedules` (`relay`, `switch`, `start_time`, `stop_time`, `enabled`)
                    VALUES (%s, %s, %s, %s, 1)""", (relay, switch, start_time, stop_time,))

        cursor.close()
        conn.commit()
        conn.close()

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
    if request.args.get('sensor') and request.args.get('start_date') and request.args.get('stop_date'):
        sensor = request.form.get("sensor")
        start_time = request.form.get("start_date")
        stop_time = request.form.get("stop_date")

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

