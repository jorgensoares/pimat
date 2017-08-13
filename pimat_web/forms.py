from flask_wtf import FlaskForm, RecaptchaField, validators
from wtforms import StringField, PasswordField, validators
from wtforms.validators import DataRequired
from pimat_web.app import app


class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])


class PasswordForgotForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])

    if app.config['RECAPTCHA'] is True:
        recaptcha = RecaptchaField('recaptcha')


class PasswordResetForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    new_password = PasswordField('new_password', [
        validators.DataRequired(),
        validators.EqualTo('verify_new_password', message='Passwords must match')
    ])
    verify_new_password = PasswordField('verify_new_password')
    token = StringField('token', validators=[DataRequired()])

    if app.config['RECAPTCHA'] is True:
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
