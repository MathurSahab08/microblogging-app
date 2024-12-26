import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

# explicitly import the contents of .env file
load_dotenv(os.path.join(basedir,'.env'))

class Config:
    # Flask and some of its extensions use the value of
    #  the secret key as a cryptographic key, useful to
    #  generate signatures or tokens.
    # to protect web forms against a nasty attack 
    # called Cross-Site Request Forgery or 
    # CSRF (pronounced "seasurf").
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_SERVER = 'smtp.sendgrid.net'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_PORT = 25
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_USERNAME = 'apikey'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_PASSWORD = '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'
    ADMINS = ['yash.mathur@alumni.stonybrook.edu']

    # pagination
    POSTS_PER_PAGE = 3