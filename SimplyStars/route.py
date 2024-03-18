# GET method typically used to request data
# POST method is used to send data to server to create/update a resource
# Login form requires the GET forms from server and POST for users to submit forms

import requests
from SimplyStars import app
from google_auth_oauthlib.flow import InstalledAppFlow
from SimplyStars.gmailAPI import send_email, generate_otp, SCOPES, filePathCred
from flask import render_template, redirect, request, url_for, jsonify, session, flash
from SimplyStars.forms import LoginForm, RegisterForm, CourseCodeForm, forgetPasswordForm, OTPForm, changePasswordForm
from SimplyStars.models import User, db, CourseCode, CourseSchedule
from flask_login import login_user, current_user
from SimplyStars.functions import html_to_json, generate_time_slots, get_schedule, get_coursename_au
from SimplyStars.automate import get_automated_schedule
import json, traceback

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

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first() #First record found
        if user and user.check_password_correction(form.password.data):
            login_user(user) # calls the load_user method and store the user'id session
            
            return redirect(url_for('main_page'))
        else:
            return jsonify({'success':False, 'error': 'Invalid username or password'})
    
    return render_template('login.html', form = form)

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm() # Forms are created and passed into html for rendering
    
    if form.validate_on_submit(): # Listens for POST submitted by forms.
        
        otp = generate_otp()
        
        session['temp_user_data'] = {
            'username': form.username.data,
            'email_address': form.email_address.data,
            'password': form.password.data,
            'otp': otp
        }
        
        send_email(form.email_address.data, otp)
        return redirect(url_for('otp_verification'))
    
    else:
        session['error_message'] = "Invalid Email or Unmatched password"

    error_message = session.pop('error_message', None)
    return render_template('register.html', form=form, error_message = error_message)

@app.route('/otp_verification', methods=['GET', 'POST'])
def otp_verification():
    form = OTPForm()

    if form.validate_on_submit():
        user_otp = form.otp.data

        # Check if the OTP matches
        if 'temp_user_data' in session and session['temp_user_data'].get('otp') == user_otp:
            # OTP is correct, proceed with user registration or next steps
            # You may want to remove the OTP from the session after successful verification
            del session['temp_user_data']['otp']
            
            new_user = User(username=session['temp_user_data'].get('username'),
                            email_address=session['temp_user_data'].get('email_address'),
                            password=session['temp_user_data'].get('password'))
            db.session.add(new_user)
            db.session.commit()
            
            return redirect(url_for('login_page'))  # Redirect to a success page or next step
        
        else:
            # OTP is incorrect, show an error message
            flash('Invalid OTP. Please try again.', 'error')

    return render_template('otp_verification.html', form=form)


@app.route('/forgetPassword', methods=['GET','POST'])
def forgetPassword_page():
    form = forgetPasswordForm()
    
    if form.validate_on_submit():
        otp = generate_otp()
        send_email(form.email_address.data, otp)
        
        session['user_data'] = {
            'email_address': form.email_address.data,
            'otp': otp
        }
        
        return redirect(url_for('otp_reset_verify'))
    
    return render_template('forgetPassword.html', form=form)

@app.route('/otp_reset_verify', methods=['GET', 'POST'])
def otp_reset_verify():
    form = OTPForm()

    if form.validate_on_submit():
        user_otp = form.otp.data

        # Check if the OTP matches
        if 'user_data' in session and session['user_data'].get('otp') == user_otp:
            # OTP is correct, proceed with user registration or next steps
            # You may want to remove the OTP from the session after successful verification
            del session['user_data']['otp']
                
            return redirect(url_for('change_password'))  # Redirect to a success page or next step
        
        else:
            # OTP is incorrect, show an error message
            flash('Invalid OTP. Please try again.', 'error')

    return render_template('otp_reset_verify.html', form=form)

@app.route('/change_password', methods=['GET','POST'])
def change_password():
    form = changePasswordForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email_address=session['user_data']['email_address']).first()
        
        user.password = form.password.data
        db.session.commit()
        session.pop('user_data', None)
        return redirect(url_for('login_page'))
            
    
    return render_template('changePassword.html', form=form)

@app.route('/main', methods=['GET', 'POST'])
def main_page():
    form = CourseCodeForm()
    print(session.get('timetable_mode'))
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

@app.route('/add_course_schedule', methods=['POST'])
def add_course_schedule():
    try:
        data = request.json

        course_code, course_name, au_value = get_coursename_au(data['html_content'])
        userId = data['user_id']
        
        course_code=CourseCode(course_code=course_code, course_name = course_name, course_au = au_value, user=userId)
        db.session.add(course_code)
        db.session.commit()
        
        json_data = json.loads(html_to_json(data['html_content']))
        for index_data in json_data:
            course_index = index_data.get('index')
            for detail in index_data['details']:
                course_detail = CourseSchedule(
                    user_id=data['user_id'],  # Assuming this is sent in the request
                    course_code=data['course_code'],  # Assuming this is sent in the request
                    course_index=course_index,
                    type=detail['type'],
                    group=detail['group'],
                    day=detail['day'],
                    time=detail['time'],
                    venue=detail['venue'],
                    remark=detail['remark']
                )
                db.session.add(course_detail)

        db.session.commit()
        
        return jsonify({'status': 'success',
                        'message': 'Course schedule added successfully.'})

    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")
        traceback.print_exc()
        return jsonify({'status': 'error',
                        'message': 'An error occurred while adding the course schedule.'}), 500

@app.route('/delete_course/<string:course_code>', methods=['POST'])
def delete_course(course_code):
    
    course = CourseCode.query.filter_by(course_code=course_code, user=current_user.id).first()
    db.session.delete(course)
    db.session.commit()
    
    course_Schedule = CourseSchedule.query.filter_by(course_code=course_code, user_id=current_user.id).all()
    for records in course_Schedule:
        db.session.delete(records)

    db.session.commit()
    
    coursecode = CourseCode.query.filter_by(user=current_user.id).all()
    if not coursecode:
        session['timetable_mode'] = 'default'
        return redirect(url_for('main_page'))
        
    if session.get('timetable_mode') == 'automated' and coursecode:
        automated_results = get_automated_schedule(current_user.id, session.get('time_preference'), session.get('day_preference'))
        session['weekly_schedules'] = json.dumps(automated_results[0])

    return redirect(url_for('main_page'))

@app.route('/delete', methods=['POST'])
def delete():
    
    if session['timetable_mode'] == 'automated':
        try:
            session['timetable_mode'] = 'default'
            db.session.query(CourseCode).delete()
            db.session.query(CourseSchedule).delete()
            db.session.commit()
            automated_results = get_automated_schedule(current_user.id, session.get('time_preference'), session.get('day_preference'))
            session['weekly_schedules'] = json.dumps(automated_results[0])
            
            return redirect(url_for(main_page))
        except Exception as e:
            db.session.rollback()
    try:
        db.session.query(CourseCode).delete()
        db.session.query(CourseSchedule).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        
    return redirect(url_for('main_page'))

@app.route('/set_time_preference', methods=['POST'])
def set_time_preference():
    data = request.json
    time_preference = data.get('time')
    session['time_preference'] = time_preference
    

    return jsonify({"message": "Time preference received"}), 200

@app.route('/set_day_preference', methods=['POST'])
def set_day_preference():
    data = request.get_json()
    day_preference = data['num_days']
    session['day_preference'] = day_preference
    
    return jsonify({"message": "Selection updated", "selectedDays": day_preference})

@app.route('/automate_timetable', methods=['GET'])
def automate_timetable():
    
    coursecode = CourseCode.query.filter_by(user=current_user.id).all()
    if not coursecode:

        return jsonify({'status': 'error', 'message': 'Automation unsuccessfully'})
    
    time_preference = session.get('time_preference')
    day_preference = session.get('day_preference')
    
    if not time_preference and not day_preference:
        return jsonify({'status': 'error', 'message': 'No preference selected'})

    session['timetable_mode'] = 'automated'

    automated_results = get_automated_schedule(current_user.id, time_preference, day_preference)
    session['weekly_schedules'] = json.dumps(automated_results[0])

    if automated_results[1] == False:
        session['timetable_mode'] = 'default'
        del session['weekly_schedules']
        return jsonify({'status': 'error', 'message': 'Automation unsuccessfully'})
    else:
        
        return jsonify({'status': 'success', 'message': 'Automation completed successfully'})
