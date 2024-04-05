# GET method typically used to request data
# POST method is used to send data to server to create/update a resource
# Login form requires the GET forms from server and POST for users to submit forms

import requests
from SimplyStars import app
from google_auth_oauthlib.flow import InstalledAppFlow
from SimplyStars.NetworkController import SCOPES, filePathCred
from flask import redirect, render_template, request, jsonify, session, json, url_for
from SimplyStars.forms import CourseCodeForm, LoginForm
from SimplyStars.models import CourseCode, User
from flask_login import current_user, login_user, logout_user
from SimplyStars.functions import generate_time_slots, get_schedule

from SimplyStars.AutomationController import automation
from SimplyStars.AccountController import accounts
from SimplyStars.ScheduleController import schedules
from SimplyStars.PreferenceController import preferences

app.register_blueprint(accounts, url_prefix='/')
app.register_blueprint(schedules, url_prefix='/')
app.register_blueprint(automation, url_prefix='/')
app.register_blueprint(preferences, url_prefix='/')

login_attempts = {}

@app.route('/')
@app.route('/home', methods=['GET']) # GET method -> Browser requests for a html file
def home_page():
    
    if 'code' in request.args:
        code = request.args['code']
        try:
            flow = InstalledAppFlow.from_client_secrets_file(filePathCred, SCOPES)
            flow.fetch_token(code=code)
            
            creds = flow.credentials
            token_json_path = 'token.json'
            with open(token_json_path, 'w') as token:
                token.write(creds.to_json())

            # Redirect or notify the user of successful authorization
            return "Authorization successful, you can now use the application."
        except Exception as e:
            # Handle exceptions and errors
            return f"An error occurred: {e}"
    else:
        # Normal behavior when there's no authorization code in the query string
        return render_template('home.html')

@app.route('/main', methods=['GET', 'POST'])
def main_page():
    form = CourseCodeForm()
    session['time_preference'] = None
    if session.get('timetable_mode') == 'automated':
        weekly_schedules = json.loads(session.get('weekly_schedules'))
    else:
        weekly_schedules = get_schedule(current_user.id)
        
    if form.validate_on_submit():
        
        exists_course = CourseCode.query.filter_by(course_code=form.course_code.data, user=current_user.id).first()
        if exists_course:
            # Jsonify is used to convert python dict to JSON and the response is sent back
            return jsonify({'status': 'error', 'message': 'Course already added'})
        else:
            # Create an instance of coursecode not coursecode form
            
            php_endpoint = "http://127.0.0.1:80/course_schedule.php"
            payload = {
                'course_code': form.course_code.data,
                'user_id' : current_user.id
            }
        
            response = requests.post(php_endpoint, data=payload)
        
            if response.status_code == 200:
                if "OK" in response.text:
                 
                    return jsonify({'status': 'success'})

                else:
                    print("PHP script did not execute as expected. Response:", response.text)
            else:
                print("Failed to make a request to the PHP script. Status Code:", response.status_code)
        
            return jsonify({'status': 'success'})
        
    schedule = generate_time_slots('8:30 AM', '10:30 PM', 50) 
    user_courses = CourseCode.query.filter_by(user=current_user.id).all()
    return render_template('main.html', form=form, user_courses=user_courses, schedule=schedule, weekly_schedules=weekly_schedules)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        username = form.username.data

        # Initialize login_attempts for the user if not already done
        if username not in login_attempts:
            login_attempts[username] = 0

        # Check for exceeded login attempts
        if login_attempts[username] >= 3:
            return jsonify({'success': False, 'error': 'Exceed Login Attempts! Please reset password'})

        # Check user credentials
        user = User.query.filter_by(username=username).first()  # First record found
        if user and user.check_password_correction(form.password.data):
            login_attempts[username] = 0  # Reset login attempts on successful login
            login_user(user)  # Log in the user
            return jsonify({'success': True})  # Redirect handled by AJAX
        else:
            login_attempts[username] += 1
            return jsonify({'success': False, 'error': 'Invalid username or password'})

    # For GET or failed POST requests
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET','POST'])
def logout():
    logout_user()
    return redirect(url_for('login_page'))