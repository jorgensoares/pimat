#!/usr/bin/python
import configparser
from flask import Flask, request, redirect
from flask import render_template
from flask import url_for

from pimat_server.relays import Relays, get_pin_status
#from core.scheduler import add_schedule

relay_config = configparser.ConfigParser()
relay_config.read('/opt/pimat/relays.ini')

app = Flask(__name__)


@app.route("/")
def main():
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

    return render_template('index.html', pins=relay_pins, status=relay_status)


@app.route("/schedule/add", methods=['POST', 'GET'])
def add_new_schedule():
    if request.method == 'POST':
        relay = request.form.get("relay")
        start_time = request.form.get("start_time")
        stop_time = request.form.get("stop_time")

    else:
        return render_template('schedules.html')


@app.route("/relays/<action>/<relay>", methods=['POST'])
def switch_relay(action, relay):
    if action and relay:

        pin = relay_config['pins'][relay]

        if action == 'on':
            relay_object = Relays(relay, pin)
            relay_object.start()
            return url_for('main')

        elif action == 'off':
            relay_object = Relays(relay, pin)
            relay_object.stop()
            return url_for('main')

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
    with open("/opt/pimat/sensors.log", "r") as f:
        content = f.read()
    return render_template('logs.html', content=content)


if __name__ == "__main__":
    app.run()
