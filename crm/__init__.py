from socket import SocketIO
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from crm.models import User, db
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_uploads import IMAGES, UploadSet, configure_uploads, patch_request_class
import os
from celery import Celery
from flask_socketio import SocketIO


def make_celery(app):
    celery = Celery(app.import_name)
    celery.conf.update(app.config["CELERY_CONFIG"])

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__, template_folder='templates')
app.config["SECRET_KEY"] = "74fe13370e062efda7e52bc7aa7336c2" 
conn = 'mysql+mysqlconnector://root:123456@localhost/northwind'
app.config['SQLALCHEMY_DATABASE_URI'] = conn
app.config['UPLOADED_PHOTOS_DEST'] = os.path.join(basedir,'static/img')

app.config.update(CELERY_CONFIG={
    'broker_url': 'redis://localhost:6379',
    'result_backend': 'redis://localhost:6379',
})

# app.config['CELERYBEAT_SCHEDULE'] = {
#     'send-daily-mail' : {
#         'task' : 'send_daily_mail',
#         'schedule' : crontab(minute = "*/1")
#     },
# }

celery_app = make_celery(app)
socketio = SocketIO(app)
photos = UploadSet('photos', IMAGES)
configure_uploads(app,photos)
patch_request_class(app)
db.app = app
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'virashopinfo@gmail.com'
app.config['MAIL_PASSWORD'] = ''
mail = Mail(app)


from crm import routes

