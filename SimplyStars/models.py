from SimplyStars import db, login_manager
from SimplyStars import bcrypt
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length = 30), nullable=False)
    email_address = db.Column(db.String(length = 50), nullable=False, unique=True)
    password_hash = db.Column(db.String(length = 60), nullable=False)
    
    @property # a decorator to define a getter method 
    def password(self):
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter # a decorator to set the password, this method is invoked when you set the password attribute
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')
    
    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)
    
class CourseCode(db.Model):
    __tablename__ = 'course_code'
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(100), nullable=False)
    user = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class CourseSchedule(db.Model):
    __tablename__ = 'course_schedule'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_code = db.Column(db.String(100), nullable=False)
    course_index = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(120))
    group = db.Column(db.String(120))
    day = db.Column(db.String(120))
    time = db.Column(db.String(120))
    venue = db.Column(db.String(120))
    remark = db.Column(db.Text)

    

