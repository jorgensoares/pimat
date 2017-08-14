import configparser
config = configparser.ConfigParser()
config.read('/opt/pimat/config.ini')


SERVER_IP = config['pimat']['server_ip']
LOG = config['pimat']['log']
UPLOAD_FOLDER = config['pimat']['upload_folder']
RELAY_CONFIG= config['pimat']['relay_config']
SQLALCHEMY_DATABASE_URI = config['pimat']['sqlalchemy_database_uri']
SQLALCHEMY_TRACK_MODIFICATIONS = config['pimat']['sqlalchemy_track_modifications']
SQLALCHEMY_ECHO = config['pimat']['sqlalchemy_echo']
MAIL_SERVER = config['pimat']['mail_server']
MAIL_PORT = int(config['pimat']['mail_port'])
MAIL_USERNAME = config['pimat']['mail_username']
MAIL_PASSWORD = config['pimat']['mail_password']
MAIL_USE_TLS = config['pimat']['mail_use_tls']
MAIL_USE_SSL = config['pimat']['mail_use_ssl']
MAIL_DEFAULT_SENDER = config['pimat']['mail_default_sender']
CSRF_ENABLED = config['pimat']['csrf_enabled']
RECAPTCHA = config['pimat']['recaptcha']
RECAPTCHA_PUBLIC_KEY = config['pimat']['recaptcha_public_key']
RECAPTCHA_PRIVATE_KEY = config['pimat']['recaptcha_private_key']
SECRET_KEY = config['pimat']['secret_key']
