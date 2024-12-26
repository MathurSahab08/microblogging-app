
# 'Flask' class is imported from flask package
from flask import Flask
import os
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import SMTPHandler
from logging.handlers import RotatingFileHandler
from flask_mail import Mail
from flask_moment import Moment
# from flask_babel import  lazy_gettext as _l


# def get_locale():
#     return request.accept_languages.best_match(current_app.config['LANGUAGES'])

print("no init")

# all below instances are created in global scope first
db = SQLAlchemy()
migrate = Migrate()
login=LoginManager()
login.login_view='auth.login'
login.login_message = ('Please log in to access this page.')
mail = Mail()

# implement datetime func. from moment.js
moment= Moment()
#babel = Babel()

print("init")
#add a function called create_app() that constructs a Flask application instance, 
# and eliminate the global variable (to facilitate testing)
def create_app(config_class=Config):

    # The __name__ variable passed to the Flask class is a Python predefined variable, 
    # which is set to the name of the module in which it is used
    app = Flask(__name__)
    app.config.from_object(config_class)

    print(app.name)
    print("name of current virtual environment is --> ", os.environ.get('VIRTUAL_ENV'))

    # .init_app() used to bind the extension instances with the application
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    #babel.init_app(app, locale_selector=get_locale)

    # register Blueprint
    from Y.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    # added URL prefix 
    from Y.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from Y.main import bp as main_bp
    app.register_blueprint(main_bp)

    from Y.cli import bp as cli_bp
    app.register_blueprint(cli_bp)

    # email logs disabled when dubug mode is on
    if not app.debug and not app.testing:

        # logging for emails
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            secure = None
            if app.config['MAIL_USE_TLS']:
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                fromaddr='no-reply@' + app.config['MAIL_SERVER'],
                toaddrs=app.config['ADMINS'], subject='Microblog Failure',
                credentials=auth, secure=secure)
            
            #sets level to only log errors, not warnings or other messages
            mail_handler.setLevel(logging.ERROR)

            # app.logger is a Flask logger object
            app.logger.addHandler(mail_handler)

            # logging to a file
            if not os.path.exists('logs'):
                os.mkdir('logs')
                file_handler = RotatingFileHandler('logs/microblog.log', maxBytes=10240, backupCount=10)
                file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
                file_handler.setLevel(logging.INFO)
                app.logger.addHandler(file_handler)
                app.logger.setLevel(logging.INFO)
                app.logger.info('Microblog startup')

    return app
            
# The bottom import is a well known workaround that avoids circular imports, 
# a common problem with Flask applications.
from Y import  models