from flask_wtf import FlaskForm, RecaptchaField, validators
from scipy.weave.accelerate_tools import Integer
from wtforms import StringField, PasswordField, validators, IntegerField
from wtforms.validators import DataRequired
import configparser
config = configparser.ConfigParser()
config.read('/opt/pimat/config.ini')


class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])


class PasswordForgotForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])

    if config['pimat']['recaptcha'] == 'True':
        recaptcha = RecaptchaField('recaptcha')


class PasswordResetForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    new_password = PasswordField('new_password', [
        validators.DataRequired(),
        validators.EqualTo('verify_new_password', message='Passwords must match')
    ])
    verify_new_password = PasswordField('verify_new_password')
    token = StringField('token', validators=[DataRequired()])

    if config['pimat']['recaptcha'] == 'True':
        recaptcha = RecaptchaField('recaptcha')


class CreateUserForm(FlaskForm):
    first_name = StringField('first_name', validators=[DataRequired()])
    last_name = StringField('last_name', validators=[DataRequired()])
    username = StringField('username', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('new_password', [
        validators.DataRequired(),
        validators.EqualTo('verify_password', message='Passwords must match')
    ])
    verify_password = PasswordField('verify_password')
    role = StringField('role')


class UpdateProfileForm(FlaskForm):
    first_name = StringField('first_name', validators=[DataRequired()])
    email = StringField('email', validators=[DataRequired()])
    last_name = StringField('last_name', validators=[DataRequired()])
    email_alerts = StringField('email_alerts')
    sms_alerts = StringField('sms_alerts')
    phone = StringField('phone')


class UpdateSettingsForm(FlaskForm):
    server_ip = StringField('server_ip', validators=[DataRequired()])
    relay_config = StringField('relay_config', validators=[DataRequired()])
    log = StringField('log', validators=[DataRequired()])
    upload_folder = StringField('upload_folder', validators=[DataRequired()])
    temp_sensor = IntegerField('temp_sensor', validators=[DataRequired()])
    ldr_sensor = IntegerField('ldr_sensor', validators=[DataRequired()])
    recaptcha_public_key = PasswordField('recaptcha_public_key')
    recaptcha_private_key = PasswordField('recaptcha_private_key')
    secret_key = PasswordField('secret_key')
    debug = StringField('debug')
    recaptcha = StringField('recaptcha')
    db_server = StringField('db_server', validators=[DataRequired()])
    db_port = IntegerField('db_port')
    db_username = StringField('db_username')
    db_password = PasswordField('db_password')
    db_name = StringField('db_name')
    db_type = StringField('db_type')
    mail_server = StringField('mail_server')
    mail_port = IntegerField('mail_port')
    mail_username = StringField('mail_username')
    mail_default_sender = StringField('mail_default_sender')
    mail_password = PasswordField('mail_password')
    mail_use_ssl = StringField('mail_use_ssl')
    mail_use_tls = StringField('mail_use_tls')


