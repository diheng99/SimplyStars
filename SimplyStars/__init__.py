#   Initializer file for Flask application
#   Flask is the main framework, SQLAlchemy is the DB flask interacts with
#   Bcrypt is used for password hashing, LoginManager is used for user authen


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate

# Creates an instance of the Flask App
app = Flask(__name__)
app.config['LOGIN_ATTEMPTS'] = {}

# Sets up database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///SimplyStars.db'
app.config['SECRET_KEY']='680d06223bae899ff44a5790'
# Makes the application context globally available
app.app_context().push()

# INIT database with Flask App
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'AccountController.login_page'

# Import the models before creating the database
from SimplyStars.models import*
#db.drop_all()
db.create_all()

from SimplyStars import route