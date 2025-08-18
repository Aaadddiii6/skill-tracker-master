from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Trainer, Course, db  # Your SQLAlchemy models and DB session
from sqlalchemy import or_

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Dashboard - show counts dynamically per user
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Query course status counts for all courses (admin can see all)
    requested_count = Course.query.filter_by(status='Requested').count()
    in_review_count = Course.query.filter_by(status='In Review').count()
    approved_count = Course.query.filter_by(status='Approved').count()
    completed_count = Course.query.filter_by(status='Completed').count()

    return render_template(
        'admin_dashboard.html',
        requested_count=requested_count,
        in_review_count=in_review_count,
        approved_count=approved_count,
        completed_count=completed_count
    )

# Manage Trainers - list, add, edit, deactivate
@admin_bp.route('/trainers', methods=['GET', 'POST'])
@login_required
def manage_trainers():
    search_query = request.args.get('q', '').strip()
    if request.method == 'POST':
        # Add new trainer owned by user
        trainer_name = request.form.get('trainer_name')
        if trainer_name:
            new_trainer = Trainer(name=trainer_name, user_id=current_user.id, status='Active')
            db.session.add(new_trainer)
            db.session.commit()
            flash('Trainer added successfully', 'success')
            return redirect(url_for('admin.manage_trainers'))

    # Filter trainers by search and user ownership
    query = Trainer.query.filter_by(user_id=current_user.id)
    if search_query:
        query = query.filter(Trainer.name.ilike(f'%{search_query}%'))
    trainers = query.all()

    return render_template('admin_trainers.html', trainers=trainers)

# Edit Trainer (example of patch/edit)
@admin_bp.route('/trainers/<uuid:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_trainer(id):
    trainer = Trainer.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    if request.method == 'POST':
        trainer.name = request.form.get('name', trainer.name)
        status = request.form.get('status')
        if status in ['Active', 'Inactive']:
            trainer.status = status
        db.session.commit()
        flash('Trainer updated successfully', 'success')
        return redirect(url_for('admin.manage_trainers'))

    return render_template('edit_trainer.html', trainer=trainer)

# Request New Course form and submission
@admin_bp.route('/courses/request', methods=['GET', 'POST'])
@login_required
def request_course():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        trainer_id = request.form.get('trainer', None)

        new_course = Course(
            title=title,
            description=description,
            user_id=current_user.id,
            trainer_id=trainer_id if trainer_id else None,
            status='Requested'
        )
        db.session.add(new_course)
        db.session.commit()
        flash('Course request submitted', 'success')
        return redirect(url_for('admin.dashboard'))

    # For the form select options
    trainers = Trainer.query.filter_by(user_id=current_user.id, status='Active').all()
    return render_template('admin_course_request.html', trainers=trainers)

# Assign time slot after approval
@admin_bp.route('/courses/schedule', methods=['GET', 'POST'])
@login_required
def schedule_course():
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        datetime_str = request.form.get('datetime')

        course = Course.query.filter_by(id=course_id, user_id=current_user.id).first_or_404()
        course.scheduled_time = datetime_str
        course.status = 'Approved'
        db.session.commit()
        flash('Time slot assigned successfully', 'success')
        return redirect(url_for('admin.dashboard'))

    # Courses pending scheduling (admin can see all)
    courses = Course.query.filter_by(status='In Review').all()
    return render_template('admin_schedule.html', courses=courses)

# Feedback overview
@admin_bp.route('/feedback')
@login_required
def feedback():
    # Aggregate feedback for current_user's courses (example schema)
    feedback_data = []
    courses = Course.query.filter_by(user_id=current_user.id, status='Completed').all()
    for course in courses:
        avg_rating = db.session.query(db.func.avg(course.feedbacks.rating)).filter(course.feedbacks).scalar() or 0
        comments_count = len(course.feedbacks)
        feedback_data.append({
            "course": course.title,
            "average_rating": round(avg_rating, 2),
            "comments": comments_count
        })

    return render_template('admin_feedback.html', feedback_summary=feedback_data)
