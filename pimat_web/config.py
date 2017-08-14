import configparser
config = configparser.ConfigParser()
config.read('/opt/pimat/config.ini')


SERVER_IP = config['pimat']['server_ip']
LOG = config['pimat']['log']
UPLOAD_FOLDER = config['pimat']['upload_folder']
RELAY_CONFIG= config['pimat']['relay_config']
SQLALCHEMY_DATABASE_URI = config['pimat']['sqlalchemy_database_uri']

if config['pimat']['sqlalchemy_track_modifications'] == 'True':
    SQLALCHEMY_TRACK_MODIFICATIONS = True
else:
    SQLALCHEMY_TRACK_MODIFICATIONS = False

if config['pimat']['sqlalchemy_echo'] == 'True':
    SQLALCHEMY_ECHO = True
else:
    SQLALCHEMY_ECHO = False


MAIL_SERVER = config['pimat']['mail_server']
MAIL_PORT = int(config['pimat']['mail_port'])
MAIL_USERNAME = config['pimat']['mail_username']
MAIL_PASSWORD = config['pimat']['mail_password']

if config['pimat']['mail_use_tls'] == 'True':
    MAIL_USE_TLS = True
else:
    MAIL_USE_TLS = False

if config['pimat']['mail_use_ssl'] == 'True':
    MAIL_USE_SSL = True
else:
    MAIL_USE_SSL = False

MAIL_DEFAULT_SENDER = config['pimat']['mail_default_sender']

if config['pimat']['csrf_enabled'] == 'True':
    CSRF_ENABLED = True
else:
    CSRF_ENABLED = False

if config['pimat']['recaptcha'] == 'True':
    RECAPTCHA = True
else:
    RECAPTCHA = False


RECAPTCHA_PUBLIC_KEY = config['pimat']['recaptcha_public_key']
RECAPTCHA_PRIVATE_KEY = config['pimat']['recaptcha_private_key']
SECRET_KEY = config['pimat']['secret_key']
