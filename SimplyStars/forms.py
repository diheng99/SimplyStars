# FlaskForm provides functionality for form handling and validation
# Each attributes creaates an input field

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from SimplyStars.models import User
import re

class LoginForm(FlaskForm):
    username = StringField(label='User Name:', validators=[DataRequired()])
    password = PasswordField(label='Password:', validators=[DataRequired()])
    submit = SubmitField(label='Sign in')
    
class RegisterForm(FlaskForm):
    
    def validate_password(self, password):
        password_data = password.data
        min_length = 8
        if len(password_data) < min_length:
            raise ValidationError(f'Password must be at least {min_length} characters long.')
        
        if not any(char.isdigit() for char in password_data):
            raise ValidationError('Password must contain at least 1 digit.')
        
        if not any(char.isupper() for char in password_data):
            raise ValidationError('Password must contain at least 1 uppercase letter.')
        
        special_character_regex = r"[!@#$%^&*(),.?\":{}|<>]"
        if not re.search(special_character_regex, password_data):
            raise ValidationError('Password must contain at least 1 special character (!@#$%^&*(),.?":{}|<>).')
    
    def validate_email_address(self, email_address):
        user = User.query.filter_by(email_address=email_address.data).first()
        if user:
            raise ValidationError('Email Address already exists! Please Login!.')
        
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already Taken! Please try a different username')
        
    username = StringField(label='User Name', validators=[DataRequired()])
    email_address = StringField(label='Email Address', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    confirm_password = PasswordField(label='Confirm Password', validators=[DataRequired(), 
                                    EqualTo('password', message='Passwords must match')])
    submit = SubmitField(label = "Create Account")
    
    ## Email() is a builtin validator so it will search for a method name validate_email_address
    
class CourseCodeForm(FlaskForm):
      
    course_code = StringField(label="Enter Course Code:", validators=[DataRequired()], render_kw={"placeholder": "Enter Course Code"})
    add = SubmitField("Add")
    
class forgetPasswordForm(FlaskForm):

    email_address = StringField(label='Email Address', validators=[DataRequired()], render_kw={"placeholder": "Email"})
    submit = SubmitField(label = "Reset Email")
    
class OTPForm(FlaskForm):
    otp = StringField('OTP', validators=[
        DataRequired(message='OTP is required'),
        Length(min=6, max=6, message='OTP must be 6 digits')
    ])

class changePasswordForm(FlaskForm):
    
    def validate_password(self, password):
        password_data = password.data
        min_length = 8
        if len(password_data) < min_length:
            raise ValidationError(f'Password must be at least {min_length} characters long.')
        
        if not any(char.isdigit() for char in password_data):
            raise ValidationError('Password must contain at least 1 digit.')
        
        if not any(char.isupper() for char in password_data):
            raise ValidationError('Password must contain at least 1 uppercase letter.')
        
        special_character_regex = r"[!@#$%^&*(),.?\":{}|<>]"
        if not re.search(special_character_regex, password_data):
            raise ValidationError('Password must contain at least 1 special character (!@#$%^&*(),.?":{}|<>).')
    
    password = PasswordField(label='Password', validators=[DataRequired()])
    confirm_password = PasswordField(label='Confirm Password', validators=[DataRequired(),
                                    EqualTo('password', message='Passwords must match')])
    submit = SubmitField(label='Change Password')