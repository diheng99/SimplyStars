from bs4 import BeautifulSoup
from flask import Blueprint, json, session, jsonify, request, redirect, url_for
from flask_login import current_user
from SimplyStars.AutomationController import DefaultSchedulingStrategy, SchedulerContext, AutomatedSchedulingStrategy
from SimplyStars.models import db, CourseCode, CourseSchedule
import traceback
from SimplyStars import app

schedules = Blueprint('ScheduleController', __name__)

@schedules.route('/add_course_schedule', methods=['POST'])
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

@schedules.route('/delete_course/<string:course_code>', methods=['POST'])
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
        preferences = session.get('time_preference')
        strategy = DefaultSchedulingStrategy()
        scheduler = SchedulerContext(strategy)
        schedule_result = scheduler.generate_schedule(current_user.id, preferences)
        session['weekly_schedules'] = json.dumps(schedule_result[0])
    else:
        preferences = session.get('time_preference')
        strategy = AutomatedSchedulingStrategy()
        scheduler = SchedulerContext(strategy)
        schedule_result = scheduler.generate_schedule(current_user.id, preferences)
        session['weekly_schedules'] = json.dumps(schedule_result[0])

    return redirect(url_for('main_page'))

@schedules.route('/delete', methods=['POST'])
def delete():
    
    if session['timetable_mode'] == 'automated':
        try:
            session['timetable_mode'] = 'default'
            db.session.query(CourseCode).delete()
            db.session.query(CourseSchedule).delete()
            db.session.commit()
            
            return redirect(url_for('main_page'))
        except Exception as e:
            db.session.rollback()
    try:
        db.session.query(CourseCode).delete()
        db.session.query(CourseSchedule).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        
    return redirect(url_for('main_page'))

def get_coursename_au(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    
    rows = soup.find_all('tr')
    course_code = rows[0].find_all('td')[0].text.strip()
    course_name = rows[0].find_all('td')[1].text.strip()
    au_value = rows[0].find_all('td')[2].text.strip()
    
    return course_code, course_name, au_value

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