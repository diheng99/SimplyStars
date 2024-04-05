from flask import Blueprint, request, session, jsonify

preferences = Blueprint('PreferenceController', __name__)

class Observer:
    def update(self, time_preference):
        raise NotImplementedError("Subclass must implement abstract method")

# PreferenceManager Class
class PreferenceManager:
    def __init__(self):
        self._observers = []
        self.time_preference = None

    def add_observer(self, observer):
        self._observers.append(observer)

    def remove_observer(self, observer):
        self._observers.remove(observer)

    def notify_observers(self):
        for observer in self._observers:
            observer.update(self.time_preference)

    def set_time_preference(self, time_preference):
        self.time_preference = time_preference
        self.notify_observers()
        
    # def set_day_preference(self, day_preference):  
    #     self.day_preference = day_preference
    #     self.notify_observers()

class TimeDisplay(Observer):
    def update(self, time_preference):
        print(f"Time preference updated to {time_preference}")

# class TimeDisplay(Observer): 
#     def update(self, time_preference, day_preference):
#         print(f"Time preference updated to {time_preference}, Day preference: {day_preference}")

preference_manager = PreferenceManager()
time_display = TimeDisplay()
preference_manager.add_observer(time_display)

@preferences.route('/set_time_preference', methods=['POST'])
def set_time_preference():
    data = request.json
    time_preference = data.get('time')
    session['time_preference'] = time_preference
    
    preference_manager.set_time_preference(time_preference)

    return jsonify({"message": "Time preference received"}), 200