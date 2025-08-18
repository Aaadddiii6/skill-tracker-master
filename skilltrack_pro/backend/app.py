from flask import Flask, redirect, url_for, session
from flask_login import LoginManager
from routes_admin import admin_bp
from routes_trainer import trainer_bp
from routes_observer import observer_bp
from auth import auth_bp
from models import db, User  # Import db and User model
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')  # Required for sessions

# Configure your Supabase PostgreSQL connection string here
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with app
db.init_app(app)

# Setup Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # Set your login route endpoint
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(trainer_bp)
app.register_blueprint(observer_bp)

@app.route('/')
def home():
    return redirect(url_for('auth.login'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if not exist
    app.run(debug=True)
