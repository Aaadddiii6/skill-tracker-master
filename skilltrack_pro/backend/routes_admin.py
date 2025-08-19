from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from .models import Trainer, Course, Documentation, Feedback, db  # Your SQLAlchemy models and DB session
from sqlalchemy import or_
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Dashboard - show counts dynamically per user
@admin_bp.route('/dashboard')
@login_required
def dashboard():
    # Query course status counts for all courses (admin can see all)
    requested_count = Course.query.filter_by(status='Requested').count()
    in_review_count = Course.query.filter_by(status='In Review').count()
    approved_count = Course.query.filter_by(status='Approved').count()
    rejected_count = Course.query.filter_by(status='Rejected').count()
    completed_count = Course.query.filter_by(status='Completed').count()

    return render_template(
        'admin_dashboard.html',
        requested_count=requested_count,
        in_review_count=in_review_count,
        approved_count=approved_count,
        rejected_count=rejected_count,
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

        # Admin can schedule any course, not just their own
        course = Course.query.filter_by(id=course_id, status='In Review').first_or_404()
        
        # Parse datetime string to proper DateTime object
        try:
            # Handle your timestamp format: "2025-08-19 19:46:21.800543"
            if datetime_str:
                # Try parsing with microseconds first
                try:
                    parsed_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    # Fallback to format without microseconds
                    parsed_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                
                course.scheduled_time = parsed_datetime
            else:
                course.scheduled_time = None
                
        except ValueError as e:
            flash(f'Invalid datetime format. Please use YYYY-MM-DD HH:MM:SS format. Error: {str(e)}', 'danger')
            return redirect(url_for('admin.schedule_course'))
        
        course.status = 'Approved'
        db.session.commit()
        flash('Time slot assigned successfully', 'success')
        return redirect(url_for('admin.dashboard'))

    # Courses pending scheduling (admin can see all)
    courses = Course.query.filter_by(status='In Review').all()
    return render_template('admin_schedule.html', courses=courses)

# View rejected courses for quality monitoring
@admin_bp.route('/rejected_courses')
@login_required
def rejected_courses():
    # Get all rejected courses with trainer and feedback information
    rejected_courses = (
        Course.query
        .filter_by(status='Rejected')
        .all()
    )
    
    # Get feedback for each rejected course
    course_feedback = {}
    for course in rejected_courses:
        # Get the latest documentation for this course
        latest_doc = (
            Documentation.query
            .filter_by(course_id=course.id)
            .order_by(Documentation.revision_number.desc())
            .first()
        )
        if latest_doc:
            feedbacks = Feedback.query.filter_by(documentation_id=latest_doc.id).all()
            course_feedback[course.id] = feedbacks
    
    return render_template('admin_rejected_courses.html', 
                         rejected_courses=rejected_courses, 
                         course_feedback=course_feedback)

# View approved courses page
@admin_bp.route('/approved_courses')
@login_required
def approved_courses():
    courses = Course.query.filter_by(status='Approved').all()
    # Map each course to its latest approved documentation (for link/display)
    approved_docs_map = {}
    for c in courses:
        latest_doc = (
            Documentation.query
            .filter_by(course_id=c.id, status='Approved')
            .order_by(Documentation.revision_number.desc())
            .first()
        )
        if latest_doc:
            approved_docs_map[c.id] = latest_doc
    return render_template('admin_approved_courses.html', courses=courses, approved_docs_map=approved_docs_map)

# Feedback overview
@admin_bp.route('/feedback')
@login_required
def feedback():
    # Aggregate feedback for current_user's courses
    feedback_data = []
    courses = Course.query.filter_by(user_id=current_user.id, status='Completed').all()
    for course in courses:
        # Get feedback through documentation relationship
        total_rating = 0
        total_feedback = 0
        comments_count = 0
        
        for doc in course.documents:
            for feedback in doc.feedbacks:
                if feedback.rating:
                    total_rating += feedback.rating
                    total_feedback += 1
                comments_count += 1
        
        avg_rating = round(total_rating / total_feedback, 2) if total_feedback > 0 else 0
        
        feedback_data.append({
            "course": course.title,
            "average_rating": avg_rating,
            "comments": comments_count
        })

    return render_template('admin_feedback.html', feedback_summary=feedback_data)
