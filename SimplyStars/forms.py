# FlaskForm provides functionality for form handling and validation
# Each attributes creaates an input field

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from SimplyStars.models import User

class LoginForm(FlaskForm):
    username = StringField(label='User Name:')
    password = PasswordField(label='Password:')
    submit = SubmitField(label='Sign in')
    
class RegisterForm(FlaskForm):
    
    def validate_email_address(self, email_address):
        user = User.query.filter_by(email_address=email_address.data).first()
        if user:
            raise ValidationError('Email Address already exists! Please Login')
        
    username = StringField(label='User Name', validators=[DataRequired()])
    email_address = StringField(label='Email Address', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    confirm_password = PasswordField(label='Confirm Password', validators=[DataRequired(), 
                                    EqualTo('password', message='Passwords must match')])
    submit = SubmitField(label = "Create Account")
    
    ## Email() is a builtin validator so it will search for a method name validate_email_address
    
class CourseCodeForm(FlaskForm):
      
    course_code = StringField(label="Enter Course Code", validators=[DataRequired()])
    add = SubmitField("Add")
    
class forgetPasswordForm(FlaskForm):

    email_address = StringField(label='Email Address', validators=[DataRequired()])
    submit = SubmitField(label = "Reset Email")
    
class OTPForm(FlaskForm):
    otp = StringField('OTP', validators=[
        DataRequired(message='OTP is required'),
        Length(min=6, max=6, message='OTP must be 6 digits')
    ])

class changePasswordForm(FlaskForm):
    
    password = PasswordField(label='Password', validators=[DataRequired()])
    confirm_password = PasswordField(label='Confirm Password', validators=[DataRequired(),
                                    EqualTo('password', message='Passwords must match')])
    submit = SubmitField(label='Change Password')