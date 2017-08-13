from pimat_web.app import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(255))
    email = db.Column(db.String(120))
    role = db.Column(db.String(10))
    phone = db.Column(db.String(16))
    email_alert = db.Column(db.String(3))
    sms_alert = db.Column(db.String(3))
    last_login = db.Column(db.DateTime)
    login_attempts = db.Column(db.String(2))

    def __init__(self, first_name, last_name, username, password, email, role='user', phone=None):
        self.first_name = first_name
        self.last_name = last_name
        self.username = username
        self.password = password
        self.email = email
        self.role = role
        self.phone = phone

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id
