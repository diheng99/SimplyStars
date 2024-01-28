# GET method typically used to request data
# POST method is used to send data to server to create/update a resource
# Login form requires the GET forms from server and POST for users to submit forms

from SimplyStars import app
from flask import render_template, redirect, url_for
from SimplyStars.forms import LoginForm, RegisterForm, CourseCodeForm
from SimplyStars.models import User, db, CourseCode
from flask_login import login_user, current_user

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup


@app.route('/')
@app.route('/home', methods=['GET'])
def home_page():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password_correction(form.password.data):
            login_user(user) # calls the load_user method and store the user'id session
            
            return redirect(url_for('main_page'))
    
    return render_template('login.html', form = form)

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    
    # form.validate will auto invoke customs validators and predefined validators such as Datarequired, email
    if form.validate_on_submit(): 
        new_user = User(username=form.username.data,
                        email_address=form.email_address.data,
                        password=form.password.data)
    
        db.session.add(new_user)
        db.session.commit()
        
        return redirect(url_for('login_page'))
    
    return render_template('register.html', form=form)

@app.route('/main', methods=['GET', 'POST'])
def main_page():
    form = CourseCodeForm()
    if form.validate_on_submit():
        # Create an instance of coursecode not coursecode form
        course_code=CourseCode(course_code=form.course_code.data, user=current_user.id)
        db.session.add(course_code)
        db.session.commit()
            
    user_courses = CourseCode.query.filter_by(user=current_user.id).all()
    
    return render_template('main.html', form=form, user_courses=user_courses)