# GET method typically used to request data
# POST method is used to send data to server to create/update a resource
# Login form requires the GET forms from server and POST for users to submit forms

import requests
from SimplyStars import app
from flask import render_template, redirect, request, url_for, jsonify
from SimplyStars.forms import LoginForm, RegisterForm, CourseCodeForm
from SimplyStars.models import User, db, CourseCode, CourseSchedule
from flask_login import login_user, current_user
from bs4 import BeautifulSoup
import json, traceback
from datetime import timedelta, datetime

@app.route('/')
@app.route('/home', methods=['GET']) # GET method -> Browser requests for a html file
def home_page():
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
    weekly_schedules = get_schedule(current_user.id)
    print(weekly_schedules)

    if form.validate_on_submit():
        
        exists_course = CourseCode.query.filter_by(course_code=form.course_code.data, user=current_user.id).first()
        if exists_course:
            # Jsonify is used to convert python dict to JSON and the response is sent back
            return jsonify({'status': 'error', 'message': 'Course already added'})
        else:
            # Create an instance of coursecode not coursecode form
            course_code=CourseCode(course_code=form.course_code.data, user=current_user.id)
            db.session.add(course_code)
            db.session.commit()

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
        
            return jsonify({'status': 'success', 'new_course': course_code.course_code})
        
    schedule = generate_time_slots('8:30 AM', '10:30 PM', 50) 
    print(schedule)
    user_courses = CourseCode.query.filter_by(user=current_user.id).all()
    return render_template('main.html', form=form, user_courses=user_courses, schedule=schedule, weekly_schedules=weekly_schedules)

@app.route('/add_course_schedule', methods=['POST'])
def add_course_schedule():
    try:
        data = request.json
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
    
def html_to_json(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    
    courses = []
    
    current_course = None
    
    for row in soup.find_all('tr'):
        columns = row.find_all('td')
        
        if columns and columns[0].get_text(strip=True).isdigit():
            
            current_course = {
                'index':columns[0].get_text(strip=True),
                'details': []
            }
            courses.append(current_course)
        
        if current_course:
            details = {
                'type': columns[1].get_text(strip=True) if len(columns) > 1 else "",
                'group': columns[2].get_text(strip=True) if len(columns) > 2 else "",
                'day': columns[3].get_text(strip=True) if len(columns) > 3 else "",
                'time': columns[4].get_text(strip=True) if len(columns) > 4 else "",
                'venue': columns[5].get_text(strip=True) if len(columns) > 5 else "",
                'remark': columns[6].get_text(strip=True) if len(columns) > 6 else "",
            }
            if any(details.values()):
                current_course['details'].append(details)
    ## JSON DUMPS CONVERTS PYTHON OBJECT TO STRINGS
    ## USE LOADS TO PARSE STRING BACK TO OBJECT 
    ## OBJECTS CAN BE REFERENCED 
    json_data = json.dumps(courses, indent=4)
    return json_data

def generate_time_slots(start_time, end_time, interval):
    time_slots = []
    current_time = datetime.strptime(start_time, '%I:%M %p')
    end_time = datetime.strptime(end_time, '%I:%M %p')
    while current_time + timedelta(minutes=interval) <= end_time:
        end_interval_time = current_time + timedelta(minutes=interval)
        formatted_slot = current_time.strftime('%H%M') + '-' + end_interval_time.strftime('%H%M')
        time_slots.append(formatted_slot)
        current_time = (current_time + timedelta(hours=1)).replace(minute=current_time.minute)
    return time_slots

def get_schedule(user_id):
 
    weekly_schedule_types = {
        'MON': {},
        'TUE': {},
        'WED': {},
        'THU': {},
        'FRI': {}
    }
    
    course_codes = (db.session.query(CourseSchedule.course_code)
                    .filter_by(user_id=user_id)
                    .group_by(CourseSchedule.course_code)
                    .all())
    
    for course_code_tuple in course_codes:
        course_code = course_code_tuple[0]
        
        course_index = (db.session.query(CourseSchedule.course_index)
                        .filter_by(user_id=user_id, course_code=course_code)
                        .group_by(CourseSchedule.course_index)
                        .all())
        
        for index_tuple in course_index:
            current_index = index_tuple[0]
            if clash_free(current_index, weekly_schedule_types, user_id, course_code):
                populate_schedule(current_index, weekly_schedule_types, user_id, course_code)
                break
            
    return weekly_schedule_types

def clash_free(current_index, weekly_schedule, user_id, course_code):
    index_details = CourseSchedule.query.filter_by(user_id=user_id,
                                                   course_code=course_code,
                                                   course_index=current_index).all()
     
    for details in index_details:
         day = details.day
         time = details.time
         if details.venue == "online":
             continue
         if day in weekly_schedule and time in weekly_schedule[day]:
             return False
         
    return True   

def format_time(time_obj):
    return time_obj.strftime('%H%M')

def populate_schedule(current_index, weekly_schedule, user_id, course_code):
    index_details = CourseSchedule.query.filter_by(user_id=user_id,
                                                   course_code=course_code,
                                                   course_index=current_index).all()
    
    for details in index_details:
        # Split the time string into start and end times
        start_time_str, end_time_str = details.time.split('-')
        start_time = datetime.strptime(start_time_str, '%H%M')
        end_time = datetime.strptime(end_time_str, '%H%M')

        while start_time + timedelta(minutes=50) <= end_time:
            end_interval_time = start_time + timedelta(minutes=50)
            time_slot = format_time(start_time) + '-' + format_time(end_interval_time)
            
            class_details = {
                'type': details.type,
                'index': details.course_index,
                'group': details.group,
                'venue': details.venue,
                'remarks': details.remark
            }
            
            if time_slot in weekly_schedule[details.day] and details.venue == "ONLINE":
                existing_entry = weekly_schedule[details.day][time_slot]
                if isinstance(existing_entry, dict):
                    weekly_schedule[details.day][time_slot] = [existing_entry, class_details]
                elif isinstance(existing_entry, list):
                    weekly_schedule[details.day][time_slot].append(class_details)
            else: 
                weekly_schedule[details.day][time_slot] = []
                weekly_schedule[details.day][time_slot].append(class_details)
            # Move to the next interval
            start_time = end_interval_time + timedelta(minutes=10)

@app.route('/delete', methods=['POST'])
def delete():
    try:
        db.session.query(CourseCode).delete()
        db.session.query(CourseSchedule).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        
    return redirect(url_for('main_page'))