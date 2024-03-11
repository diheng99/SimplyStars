from bs4 import BeautifulSoup
from datetime import timedelta, datetime
from SimplyStars.models import db, CourseSchedule
import json

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
    odd = "Teaching Wk1,3,5,7,9,11,13"
    even = "Teaching Wk2,4,6,8,10,12"
     
    for details in index_details:
         day = details.day
         time = details.time

         if details.venue == "online":
             continue
         if day in weekly_schedule and time in weekly_schedule[day]:
             
             scheduled_class = weekly_schedule[day][time]
             for classes in scheduled_class:
                 if classes['remarks'] != odd and classes['remarks'] != even:
                     return False
                 
                 if classes['remarks'] == odd and details.remarks == odd:
                     return False
                 
                 if classes['remarks'] == even and details.remarks == even:
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
            
            if time_slot in weekly_schedule[details.day] and details.venue:
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
