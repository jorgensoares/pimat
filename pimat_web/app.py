#!/usr/bin/python
from flask_principal import Principal, Identity, AnonymousIdentity, identity_changed, identity_loaded, RoleNeed, \
    UserNeed, Permission
from functions import get_previous_date, get_now, sigterm_handler, allowed_file, convert_bytes, convert_timestamp
from forms import LoginForm, PasswordForgotForm, PasswordResetForm, CreateUserForm, UpdateProfileForm, UpdateSettingsForm
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired
from flask import Flask, request, redirect, render_template, flash, url_for, current_app, session
from werkzeug.security import generate_password_hash, check_password_hash
from api import SensorsAPI, SchedulesAPI, RelayLoggerAPI, MonitoringAPI
from models import db, User, Sensors, Schedules, RelayLogger, Monitoring
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail, Message
from config import config as pimat_config, config_file
from version import __version__
from flask_restful import Api
from flask_login import *
import configparser
import logging
import signal
import requests
import json
import os

version = __version__

app = Flask(__name__)
app.config.from_object('config')

db.init_app(app)
csrf = CSRFProtect(app)
api = Api(app, decorators=[csrf.exempt])
mail = Mail()
Principal(app)
file_handler = logging.FileHandler(app.config['LOG'])
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
admin_permission = Permission(RoleNeed('admin'))
login_manager = LoginManager()
login_manager.init_app(app)
mail.init_app(app)
relay_config = configparser.ConfigParser()
relay_config.read(app.config['RELAY_CONFIG'])
api.add_resource(SensorsAPI, '/api/sensors')
api.add_resource(SchedulesAPI, '/api/schedules')
api.add_resource(RelayLoggerAPI, '/api/v1/relay/logger')
api.add_resource(MonitoringAPI, '/api/v1/monitoring')


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    # Set the identity user object
    identity.user = current_user
    if hasattr(current_user, 'id'):
        identity.provides.add(UserNeed(current_user.id))
    if hasattr(current_user, 'role'):
        identity.provides.add(RoleNeed(current_user.role))


@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for("login"))


@app.errorhandler(404)
@login_required
def not_found(error):
    clients = pimat_config['clients']
    return render_template('error.html', error=error, clients=clients, version=version)


@app.before_first_request
def create_db():
    db.create_all()
    if not User.query.filter(User.username == 'admin').first():
        user = User('Pimat',
                    'Web',
                    'admin',
                    'pbkdf2:sha256:50000$QZildwvb$ec2954dfe34d5a540d1aa9b64ce8628ab34b4f8d64a04208f15082a431bc5631',
                    'change@me.com',
                    'admin')
        db.session.add(user)
        db.session.commit()


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    else:
        return render_template("login.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=True)
                user.last_login = get_now()
                user.login_attempts = 0
                db.session.commit()
                identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
                flash('Welcome {0} {1}'.format(user.first_name, user.last_name), 'success')
                return redirect(url_for("index"))
            else:
                flash('Wrong Password', 'danger')
                failed_attempts = int(user.login_attempts)
                failed_attempts += 1
                user.login_attempts = failed_attempts
                db.session.commit()
                return render_template("login.html", form=form)
        else:
            flash('User not found!', 'warning')
            return render_template("login.html", form=form)
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'warning')

    return render_template("login.html", form=form)


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    for key in ('identity.name', 'identity.auth_type'):
        session.pop(key, None)
    identity_changed.send(current_app._get_current_object(), identity=AnonymousIdentity())
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    clients = pimat_config['clients']

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

    sensors_data = Sensors.query.filter(Sensors.timestamp.between(get_previous_date(1), get_now())). \
        order_by(Sensors.timestamp.asc()).all()
    relay_log = RelayLogger.query.filter(RelayLogger.timestamp.between(get_previous_date(1), get_now())). \
        order_by(RelayLogger.timestamp.asc()).all()

    return render_template('index.html',
                           version=version,
                           relay_config=relay_config,
                           status=relay_status,
                           sensors_data=sensors_data,
                           schedules=Schedules.query.order_by(Schedules.relay.asc()).all(),
                           last_reading=Sensors.query.order_by(Sensors.timestamp.desc()).first(),
                           relay_log=relay_log,
                           clients=clients,
                           config=pimat_config
                           )


@app.route("/relays", methods=['GET'])
@login_required
def relays():
    clients = pimat_config['clients']
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

    relay_log = RelayLogger.query.filter(RelayLogger.timestamp.between(get_previous_date(1), get_now())). \
        order_by(RelayLogger.timestamp.asc()).all()

    return render_template('relays.html',
                           version=version,
                           status=relay_status,
                           schedules=Schedules.query.order_by(Schedules.relay.asc()).all(),
                           relay_log=relay_log,
                           clients=clients,
                           )

@app.route("/schedule/<action>/<schedule_id>", methods=['POST', 'GET'])
@login_required
def add_new_schedule(action, schedule_id):
    clients = pimat_config['clients']
    if request.method == 'POST' and action == 'add':
        relay = request.form.get("relay")
        start_time = request.form.get("start_time")
        stop_time = request.form.get("stop_time")

        if start_time >= stop_time:
            flash('The stop time cannot be equal or smaller than the start time, please try again!', 'warning')
            return render_template('schedules.html', clients=clients, version=version, schedule=None)

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
        json_data = dict()
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
            return 404

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
            return render_template('schedules.html', clients=clients, version=version, schedule=None)

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
        return render_template('schedules.html', clients=clients, version=version, schedule=schedule)
    else:
        return render_template('schedules.html', clients=clients, version=version, schedule=None)


@app.route("/relays/<action>/<relay>", methods=['POST'])
@login_required
def switch_relay(action, relay):
    clients = pimat_config['clients']
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
        return render_template('error.html', clients=clients, version=version, error="wrong request")


@app.route("/sensors", methods=['GET'])
@login_required
def sensors():
    clients = pimat_config['clients']
    if request.args.get('sensor') and request.args.get('dates') and request.args.get('client'):
        client = request.args.get('client')
        sensor = request.args.get("sensor")
        start_date, end_date = request.args.get("dates").split(' - ')
        end_date = '{0} 23:59:59'.format(end_date)
        sensor_column = 'sensors.%s' % sensor
        result = Sensors.query.with_entities(Sensors.timestamp, sensor_column).filter(Sensors.source == client). \
            filter(Sensors.timestamp.between(start_date, end_date)).all()

        return render_template('sensors.html',
                               version=version,
                               result=result,
                               sensor=sensor,
                               dates=request.args.get("dates"),
                               clients=clients,
                               client=client
                               )
    else:
        return render_template('sensors.html', clients=clients, version=version)


@app.route("/camera", methods=['GET'])
@login_required
def camera():
    clients = pimat_config['clients']
    return render_template('camera.html', clients=clients, version=version)


@app.route("/logs", methods=['GET'])
@login_required
def logs():
    clients = pimat_config['clients']
    with open("/var/log/pimat/pimat-server.log", "r") as f:
        pimat_server_log = f.read()
    with open("/var/log/pimat/pimat-web.log", "r") as f:
        pimat_web_log = f.read()

    return render_template('logs.html',
                           pimat_server_log=pimat_server_log,
                           pimat_web_log=pimat_web_log,
                           clients=clients,
                           version=version
                           )


@app.route("/profile", methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    clients = pimat_config['clients']

    if form.validate_on_submit():
        user = User.query.filter(User.id == current_user.id).first_or_404()
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.email = form.email.data
        user.email_alert = form.email_alerts.data
        user.sms_alert = form.sms_alerts.data
        user.phone = form.phone.data
        db.session.commit()
        flash('Profile Updated successfully', 'success')
        return redirect(url_for("profile"))

    return render_template('profile.html', clients=clients, version=version, form=form)


@app.route('/profile/picture', methods=['POST'])
@login_required
def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part', 'warning')
        return redirect(url_for("profile"))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'warning')
        return redirect(url_for("profile"))
    if file and allowed_file(file.filename):
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], current_user.username + '.png'))

    return redirect(url_for("profile"))


@app.route("/monitoring/<client>", methods=['GET'])
@login_required
def monitoring(client):
    clients = pimat_config['clients']
    last_reading = Monitoring.query.filter(Monitoring.source == client).order_by(Monitoring.timestamp.desc()).first_or_404()
    last_reading.disk_total = convert_bytes(int(last_reading.disk_total))
    last_reading.disk_used = convert_bytes(int(last_reading.disk_used))
    last_reading.disk_free = convert_bytes(int(last_reading.disk_free))
    last_reading.disk_total_boot = convert_bytes(int(last_reading.disk_total_boot))
    last_reading.disk_used_boot = convert_bytes(int(last_reading.disk_used_boot))
    last_reading.disk_free_boot = convert_bytes(int(last_reading.disk_free_boot))
    last_reading.ram_total = convert_bytes(int(last_reading.ram_total))
    last_reading.ram_used = convert_bytes(int(last_reading.ram_used))
    last_reading.ram_free = convert_bytes(int(last_reading.ram_free))
    last_reading.swap_total = convert_bytes(int(last_reading.swap_total))
    last_reading.swap_used = convert_bytes(int(last_reading.swap_used))
    last_reading.swap_free = convert_bytes(int(last_reading.swap_free))
    last_reading.eth0_received = convert_bytes(int(last_reading.eth0_received))
    last_reading.eth0_sent = convert_bytes(int(last_reading.eth0_sent))
    last_reading.wlan0_received = convert_bytes(int(last_reading.wlan0_received))
    last_reading.wlan0_sent = convert_bytes(int(last_reading.wlan0_sent))
    last_reading.lo_received = convert_bytes(int(last_reading.lo_received))
    last_reading.lo_sent = convert_bytes(int(last_reading.lo_sent))
    last_reading.boot_time = convert_timestamp(last_reading.boot_time)

    return render_template('monitoring_new.html',
                           last_reading=last_reading,
                           client=client,
                           clients=clients,
                           version=version
                           )


@app.route("/user/<action>/<user_id>", methods=['GET', 'POST'])
@admin_permission.require()
@login_required
def edit_user(action, user_id):
    form = CreateUserForm()
    clients = pimat_config['clients']

    if action == 'create' and form.validate_on_submit():
        role = form.role.data
        if role == '':
            role = 'user'

        if User.query.filter(User.username == form.username.data).all():
            flash('User already exists!', 'danger')
            return render_template('user_create.html', clients=clients, version=version)

        hashed_password = generate_password_hash(form.password.data)
        user = User(form.first_name.data, form.last_name.data, form.username.data, hashed_password, form.email.data,
                    role)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("users"))

    elif request.method == 'POST' and action == 'delete' and user_id:
        User.query.filter(User.id == user_id).delete()
        db.session.commit()
        return url_for("users")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'warning')

    return render_template('user_create.html', clients=clients, version=version, form=form)


@app.route("/users", methods=['GET'])
@admin_permission.require()
@login_required
def users():
    clients = pimat_config['clients']
    return render_template('users.html', users=User.query.order_by(User.id.asc()).all(), clients=clients, version=version)


@app.route("/password_change", methods=['GET', 'POST'])
@login_required
def password_change():
    clients = pimat_config['clients']
    if request.method == 'POST':
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        verify_new_password = request.form.get("verify_new_password")

        if current_password and new_password and verify_new_password:
            if check_password_hash(current_user.password, current_password):
                if new_password == verify_new_password:
                    user = User.query.filter(User.id == current_user.id).first_or_404()
                    user.password = generate_password_hash(new_password)
                    db.session.commit()

                    message = '''Hello %s,\n\n This is e-mail is to inform you that you have changed your password successfully.
                     \nIf this request was not made by you please contact support immediately.\n
                     \nThank you.\n Pimat\n\n''' % user.username

                    subject = "Pimat Password Change Notice - %s" % user.username
                    msg = Message(recipients=[user.email], body=message, subject=subject)
                    mail.send(msg)

                    flash('Password changed successfully, you should logout and login again!', 'success')
                    return redirect(url_for("dashboard"))
                else:
                    flash('Passwords dont Match!', 'danger')
                    return render_template('password_change.html', clients=clients, version=version)
            else:
                flash('Wrong Current Password', 'danger')
                return render_template('password_change.html', clients=clients, version=version)
        else:
            flash('All fields are mandatory!', 'danger')
            return render_template('password_change.html', clients=clients, version=version)

    return render_template('password_change.html', clients=clients, version=version)


@app.route("/password_forgot", methods=['GET', 'POST'])
def password_forgot():
    form = PasswordForgotForm()
    if form.validate_on_submit():
        user_details = User.query.filter(User.username == form.username.data).first()
        if user_details:
            s = Serializer(app.config['SECRET_KEY'], expires_in=600)
            token = s.dumps({'id': user_details.id})
            message = '''Hello, \n\n To reset your password go to: http://%s/password_reset \n\n Token: \n %s''' % \
                      (app.config['SERVER_IP'], token)
            subject = "Pimat Password Reset - %s" % user_details.username
            msg = Message(recipients=[user_details.email], body=message, subject=subject)
            mail.send(msg)
            flash('Please verify you mailbox!', 'success')
            return redirect(url_for("password_reset"))
        else:
            return render_template('password_forgot.html', version=version, form=form)
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'warning')

    return render_template('password_forgot.html', version=version, form=form)


@app.route("/password_reset", methods=['GET', 'POST'])
def password_reset():
    form = PasswordResetForm()
    if form.validate_on_submit():
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(form.token.data)
        except SignatureExpired:
            flash('Expired Token', 'danger')
            return render_template('password_reset_form.html', version=version, form=form)
        except BadSignature:
            flash('Invalid Token', 'danger')
            return render_template('password_reset_form.html', version=version, form=form)

        user = User.query.filter(User.id == data['id']).first()
        if form.username.data == user.username:
            user.password = generate_password_hash(form.new_password.data)
            db.session.commit()
            message = '''Hello %s,\n\n This is e-mail is to inform you that you have reset your password successfully. 
            \nIf this request was not made by you please contact support immediately.\n 
            \nThank you.\n Pimat\n\n''' % user.username

            subject = "Pimat Password Reset Notice - %s" % user.username
            msg = Message(recipients=[user.email], body=message, subject=subject)
            mail.send(msg)
            flash('Password updated successfully, Please login.', 'success')
            return redirect(url_for("login"))
        else:
            flash('Invalid user', 'danger')
            return render_template('password_reset_form.html', version=version, form=form)
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'warning')

    return render_template('password_reset_form.html', version=version, form=form)


@app.route("/settings", methods=['GET', 'POST'])
@admin_permission.require()
@login_required
def settings():
    form = UpdateSettingsForm()
    clients = pimat_config['clients']
    cameras = pimat_config['cameras']

    if form.validate_on_submit():
        pimat_config.set('pimat', 'server_ip', form.server_ip.data)
        pimat_config.set('pimat', 'relay_config', form.relay_config.data)
        pimat_config.set('pimat', 'log', form.log.data)
        pimat_config.set('pimat', 'upload_folder', form.upload_folder.data)
        pimat_config.set('pins', 'temp_sensor', form.temp_sensor.data)
        pimat_config.set('pins', 'ldr_sensor', form.ldr_sensor.data)
        pimat_config.set('pimat', 'recaptcha_public_key', form.recaptcha_public_key.data)
        pimat_config.set('pimat', 'recaptcha_private_key', form.recaptcha_private_key.data)
        pimat_config.set('pimat', 'secret_key', form.secret_key.data)
        pimat_config.set('pimat', 'debug', form.debug.data)
        pimat_config.set('pimat', 'recaptcha', form.recaptcha.data)
        pimat_config.set('database', 'db_server', form.db_server.data)
        pimat_config.set('database', 'db_port', form.db_port.data)
        pimat_config.set('database', 'db_username', form.db_username.data)
        pimat_config.set('database', 'db_password', form.db_password.data)
        pimat_config.set('database', 'db_name', form.db_name.data)
        pimat_config.set('database', 'db_type', form.db_type.data)
        pimat_config.set('email', 'mail_server', form.mail_server.data)
        pimat_config.set('email', 'mail_port', form.mail_port.data)
        pimat_config.set('email', 'mail_username', form.mail_username.data)
        pimat_config.set('email', 'mail_default_sender', form.mail_default_sender.data)
        pimat_config.set('email', 'mail_password', form.mail_password.data)
        pimat_config.set('email', 'mail_use_ssl', form.mail_use_ssl.data)
        pimat_config.set('email', 'mail_use_tls', form.mail_use_tls.data)
        pimat_config.set('dashboard', 'graph', form.dashboard_graph.data)
        pimat_config.set('dashboard', 'relays', form.dashboard_relays.data)
        pimat_config.set('dashboard', 'schedules', form.dashboard_schedules.data)
        pimat_config.set('dashboard', 'sensors', form.dashboard_sensors.data)
        pimat_config.set('dashboard', 'stats', form.dashboard_stats.data)
        pimat_config.set('dashboard', 'client', form.dashboard_client.data)
        if form.client_name.data:
            pimat_config.set('clients', form.client_name.data, form.client_ip.data)
        if form.camera_name.data:
            pimat_config.set('clients', form.camera_name.data, form.camera_ip.data)
        with open(config_file, 'w') as ini_file:
            pimat_config.write(ini_file)

        app.config.from_object('config')
        flash('Settings updated successfully! Some settings will only take effect after you restart Pimat.', 'success')
        return redirect(url_for("settings"))

    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'warning')

    return render_template('settings.html',
                           config=pimat_config,
                           clients=clients,
                           cameras=cameras,
                           version=version,
                           form=form
                           )


@app.route("/client/delete/<client>", methods=['POST'])
@admin_permission.require()
@login_required
def client_delete(client):
    pimat_config.remove_option('clients', client)

    with open(config_file, 'w') as ini_file:
        pimat_config.write(ini_file)

    flash('Client {0} delete successfully'.format(client), 'success')
    return redirect(url_for("settings"))


def main():
    signal.signal(signal.SIGTERM, sigterm_handler)
    app.run(host='0.0.0.0',
            port=80,
            threaded=True,
            )

if __name__ == "__main__":
    main()
