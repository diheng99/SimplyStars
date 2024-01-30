# GET method typically used to request data
# POST method is used to send data to server to create/update a resource
# Login form requires the GET forms from server and POST for users to submit forms

import requests
from SimplyStars import app
from flask import render_template, redirect, request, url_for, jsonify
from SimplyStars.forms import LoginForm, RegisterForm, CourseCodeForm
from SimplyStars.models import User, db, CourseCode, CourseSchedule
from flask_login import login_user, current_user

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
    scraped_html = None
    if form.validate_on_submit():
        # Create an instance of coursecode not coursecode form
        course_code=CourseCode(course_code=form.course_code.data, user=current_user.id)
        db.session.add(course_code)
        db.session.commit()

        php_endpoint = "http://127.0.0.1:80/course_schedule.php"
        payload = {
            'course_code': form.course_code.data
        }
        
        response = requests.post(php_endpoint, data=payload)
        
        if response.status_code == 200:
            if "OK" in response.text:
                # The PHP script executed successfully and presumably created the file
                print("PHP script executed successfully.")
            else:
                # The PHP script did not return "OK", so there may have been an issue
                print("PHP script did not execute as expected. Response:", response.text)
        else:
            print("Failed to make a request to the PHP script. Status Code:", response.status_code)
        
        
    user_courses = CourseCode.query.filter_by(user=current_user.id).all()
    
    return render_template('main.html', form=form, user_courses=user_courses, scraped_html=scraped_html)

@app.route('/add_course_schedule', methods=['POST'])
def add_course_schedule():
    print(request.headers)
    try:
        data = request.json

        course_schedule = CourseSchedule(course_code=data['course_code'], user=2, html_content=data['html_content'])

        db.session.add(course_schedule)  # Fixed typo here
        db.session.commit()
        return jsonify({"message": "Course schedule added successfully"}), 200

    except Exception as e:
        return jsonify({"Error": str(e)}), 500
    