from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
from Y import db
from Y.models import User
import sqlalchemy as sa


class RegistrationForm(FlaskForm):

    username=StringField('Username', validators=[DataRequired()])
    email= StringField("email", validators=[DataRequired(), Email()])
    password= PasswordField('Password',validators=[DataRequired()])
    password2=PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit=SubmitField('Register')

    def validate_username(self, uname):
        #user = sa.select(User).where(User.username == uname.data)
        user = User.query.filter_by(username=uname.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
        
    def validate_email(self, email):

        #user=db.session.scalar(sa.select(User).where(User.email==email.data))
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

# 'FlaskForm' is the base class
class LoginForm(FlaskForm):
    username=StringField('Username', validators=[DataRequired()])
    password=PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit=SubmitField('Sign in')

class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')


