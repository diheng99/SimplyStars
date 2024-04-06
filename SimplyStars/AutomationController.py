from flask import Blueprint, jsonify, json
from flask_login import current_user
from datetime import timedelta, datetime
from SimplyStars.models import CourseCode, db, CourseSchedule
from flask import session

automation = Blueprint('AutomationController', __name__)

class SchedulingStrategy:
    def generate_schedule(self, user_id, preferences):
        raise NotImplementedError

class AutomatedSchedulingStrategy(SchedulingStrategy):
    def generate_schedule(self, user_id, preferences):

        def clash_free(current_index, weekly_schedule, user_id, course_code):
            index_details = CourseSchedule.query.filter_by(user_id=user_id, course_code=course_code, course_index=current_index).all()
            odd = "Teaching Wk1,3,5,7,9,11,13"
            even = "Teaching Wk2,4,6,8,10,12"
            
            for details in index_details:
                day = details.day
                time = details.time

                if details.venue == "online":
                    continue
                
                start_time = int(time.split('-')[0])
                if session.get('time_preference') == 'afternoon' and start_time < 1230:
                    return False
                
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

        def populate_schedule(current_index, weekly_schedule, user_id, course_code):
            index_details = CourseSchedule.query.filter_by(user_id=user_id, course_code=course_code, course_index=current_index).all()
            
            for details in index_details:
                start_time_str, end_time_str = details.time.split('-')
                start_time = datetime.strptime(start_time_str, '%H%M')
                end_time = datetime.strptime(end_time_str, '%H%M')

                while start_time + timedelta(minutes=50) <= end_time:
                    end_interval_time = start_time + timedelta(minutes=50)
                    time_slot = format_time(start_time) + '-' + format_time(end_interval_time)
                    
                    class_details = {
                        'type': details.type,
                        'course': details.course_code,
                        'index': details.course_index,
                        'group': details.group,
                        'venue': details.venue,
                        'remarks': details.remark
                     }
                    
                    if time_slot in weekly_schedule[details.day]:
                        existing_entry = weekly_schedule[details.day][time_slot]
                        if isinstance(existing_entry, list):
                            existing_entry.append(class_details)
                    else:
                        weekly_schedule[details.day][time_slot] = [class_details]
                    
                    start_time = end_interval_time + timedelta(minutes=10)

        def format_time(time_obj):
            return time_obj.strftime('%H%M')

        # Start of the main logic for automated scheduling
        session['time_preference'] = preferences
        weekly_schedule_types = {'MON': {}, 'TUE': {}, 'WED': {}, 'THU': {}, 'FRI': {}}
        
        course_codes = (db.session.query(CourseSchedule.course_code).filter_by(user_id=user_id).group_by(CourseSchedule.course_code).all())

        for course_code_tuple in course_codes:
            course_code = course_code_tuple[0]
            result = False

            course_index = (db.session.query(CourseSchedule.course_index).filter_by(user_id=user_id, course_code=course_code).group_by(CourseSchedule.course_index).all())
            
            for index_tuple in course_index:
                current_index = index_tuple[0]
                
                if clash_free(current_index, weekly_schedule_types, user_id, course_code):
                    populate_schedule(current_index, weekly_schedule_types, user_id, course_code)
                    result = True
                    break
                
            if not result:
                return weekly_schedule_types, False
        
        return weekly_schedule_types, True

class DefaultSchedulingStrategy(SchedulingStrategy):
    def generate_schedule(self, user_id):
        
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
    
        weekly_schedule_types = {'MON': {}, 'TUE': {}, 'WED': {}, 'THU': {}, 'FRI': {}}
        course_codes = (db.session.query(CourseSchedule.course_code).filter_by(user_id=user_id).group_by(CourseSchedule.course_code).all())
    
        for course_code_tuple in course_codes:
            course_code = course_code_tuple[0]
        
            # get all unique course index 
            course_index = (db.session.query(CourseSchedule.course_index)
                        .filter_by(user_id=user_id, course_code=course_code)
                        .group_by(CourseSchedule.course_index)
                        .all())
        
            for index_tuple in course_index:
                current_index = index_tuple[0]
                if clash_free(current_index, weekly_schedule_types, user_id, course_code):
                    populate_schedule(current_index, weekly_schedule_types, user_id, course_code)
                    break
                
        return weekly_schedule_types, True
        
class SchedulerContext:
    def __init__(self, strategy: SchedulingStrategy):
        self.strategy = strategy

    def set_strategy(self, strategy: SchedulingStrategy):
        self.strategy = strategy

    def generate_schedule(self, user_id, preferences):
        return self.strategy.generate_schedule(user_id, preferences)
    
@automation.route('/automate_timetable', methods=['GET'])
def automate_timetable():
    user_id = current_user.id
    
    coursecode = CourseCode.query.filter_by(user=current_user.id).all()
    if not coursecode:
        return jsonify({'status': 'error', 'message': 'No Course Added'})
        
    preferences = session.get('time_preference')
    if not preferences:
        return jsonify({'status': 'error', 'message': 'No preference selected'})
    
    if preferences:
        strategy = AutomatedSchedulingStrategy()
    else:
        strategy = DefaultSchedulingStrategy()
    
    scheduler = SchedulerContext(strategy)
    schedule_result = scheduler.generate_schedule(user_id, preferences)

    if not schedule_result[1]:
        session['timetable_mode'] = 'default'
        return jsonify({'status': 'error', 'message': 'Automation unsuccessful'})
    else:
        session['timetable_mode'] = 'automated'
        session['weekly_schedules'] = json.dumps(schedule_result[0])
        return jsonify({'status': 'success', 'message': 'Automation completed successfully'})