import uuid
from sqlalchemy.dialects.postgresql import UUID
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supabase_user_id = db.Column(UUID(as_uuid=True), unique=True, nullable=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(50), nullable=True)

    # Relationships
    trainers = db.relationship('Trainer', backref='owner', lazy=True)
    courses = db.relationship('Course', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Trainer(db.Model):
    __tablename__ = 'trainers'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='Active')

    # Owner of the trainer (user)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)

    # Relationship to courses
    courses = db.relationship('Course', backref='trainer', lazy=True)

    def __repr__(self):
        return f'<Trainer {self.name}>'

class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='Requested')
    scheduled_time = db.Column(db.DateTime, nullable=True)

    # Owner of the course (user)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('users.id'), nullable=False)
    # Assigned trainer (UUID foreign key)
    trainer_id = db.Column(UUID(as_uuid=True), db.ForeignKey('trainers.id'), nullable=True)

    # Relationship to documentation submissions
    documents = db.relationship('Documentation', backref='course', lazy=True)

    def __repr__(self):
        return f'<Course {self.title}>'

class Documentation(db.Model):
    __tablename__ = 'documentation'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = db.Column(UUID(as_uuid=True), db.ForeignKey('courses.id'), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), default='Pending')  # Pending, Approved, Rejected, etc.
    submitted_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    approved_at = db.Column(db.DateTime, nullable=True)
    rejected_at = db.Column(db.DateTime, nullable=True)
    revision_number = db.Column(db.Integer, default=0)

    # Relationship to feedbacks about this documentation
    feedbacks = db.relationship('Feedback', backref='documentation', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Documentation {self.id} for Course {self.course_id}>'

class Feedback(db.Model):
    __tablename__ = 'feedback'

    id = db.Column(db.Integer, primary_key=True)
    documentation_id = db.Column(UUID(as_uuid=True), db.ForeignKey('documentation.id'), nullable=False)
    comments = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<Feedback {self.id} for Documentation {self.documentation_id}>'
