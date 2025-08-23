from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from .models import Trainer, Course, Documentation, Feedback, db
from sqlalchemy import or_
from datetime import datetime
from .supabase_client import supabase  # Import your initialized Supabase client

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def get_all_trainers():
    try:
        response = supabase.auth.admin.list_users()
        if response.error:
            raise Exception(response.error.message)
        # Filter users with role 'trainer' in user_metadata
        trainers = [user for user in response.data['users'] if user['user_metadata'].get('role') == 'trainer']
        return trainers
    except Exception as e:
        print(f"Failed to get trainers from Supabase: {e}")
        return []

# Dashboard - show summary counts of courses by status
@admin_bp.route('/dashboard')
@login_required
def dashboard():
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

# Manage Trainers - list (from Supabase), add new locally or via Supabase API, filter
@admin_bp.route('/trainers', methods=['GET', 'POST'])
@login_required
def manage_trainers():
    search_query = request.args.get('q', '').strip()
    if request.method == 'POST':
        trainer_name = request.form.get('trainer_name')
        trainer_email = request.form.get('trainer_email')
        # Optional: Call your add_trainer() helper here to register in Supabase Auth with role 'trainer'
        # For now, we add locally as backup or for profile storing
        if trainer_name and trainer_email:
            # You can add logic to add trainer to Supabase here
            new_trainer = Trainer(name=trainer_name, user_id=current_user.id, status='Active')
            db.session.add(new_trainer)
            db.session.commit()
            flash('Trainer added successfully', 'success')
            return redirect(url_for('admin.manage_trainers'))

    # Fetch trainers from Supabase Auth
    supabase_trainers = get_all_trainers()

    # Optionally filter trainers on name/email from Supabase list
    if search_query:
        supabase_trainers = [
            t for t in supabase_trainers if search_query.lower() in t['user_metadata'].get('username', '').lower()
            or search_query.lower() in t.get('email', '').lower()
        ]

    return render_template('admin_trainers.html', trainers=supabase_trainers)

# Edit Trainer info (local DB)
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

# Admin Course Request Form and Submission
@admin_bp.route('/courses/request', methods=['GET', 'POST'])
@login_required
def request_course():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        trainer_id = request.form.get('trainer', None)  # this is likely trainer's Supabase user id

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

    trainers = get_all_trainers()  # Get trainers live
    return render_template('admin_course_request.html', trainers=trainers)

@admin_bp.route('/courses/schedule', methods=['GET', 'POST'])
@login_required
def schedule_course():
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        datetime_str = request.form.get('datetime')

        # Fetch course owned by current admin and in 'In Review' status
        course = Course.query.filter_by(status='In Review', user_id=current_user.id).all()

        try:
            if datetime_str:
                try:
                    parsed_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    parsed_datetime = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M:%S')
                course.scheduled_time = parsed_datetime
            else:
                course.scheduled_time = None
        except ValueError as e:
            flash(f'Invalid datetime format. Use YYYY-MM-DD HH:MM:SS. Error: {str(e)}', 'danger')
            return redirect(url_for('admin.schedule_course'))

        course.status = 'Approved'
        db.session.commit()
        flash('Time slot assigned successfully', 'success')
        return redirect(url_for('admin.dashboard'))

    # List only courses added by this admin and in 'In Review'
    courses = Course.query.filter_by(status='In Review', user_id=current_user.id).all()
    return render_template('admin_schedule.html', courses=courses)


# View rejected courses and feedback
@admin_bp.route('/rejected_courses')
@login_required
def rejected_courses():
    rejected_courses = Course.query.filter_by(status='Rejected').all()

    course_feedback = {}
    for course in rejected_courses:
        latest_doc = Documentation.query.filter_by(course_id=course.id).order_by(
            Documentation.revision_number.desc()).first()
        if latest_doc:
            feedbacks = Feedback.query.filter_by(documentation_id=latest_doc.id).all()
            course_feedback[course.id] = feedbacks

    return render_template('admin_rejected_courses.html',
                           rejected_courses=rejected_courses,
                           course_feedback=course_feedback)

# View approved courses and latest approved docs
@admin_bp.route('/approved_courses')
@login_required
def approved_courses():
    courses = Course.query.filter_by(status='Approved').all()

    approved_docs_map = {}
    for c in courses:
        latest_doc = Documentation.query.filter_by(course_id=c.id, status='Approved').order_by(
            Documentation.revision_number.desc()).first()
        if latest_doc:
            approved_docs_map[c.id] = latest_doc

    return render_template('admin_approved_courses.html', courses=courses, approved_docs_map=approved_docs_map)

# Feedback summary page
@admin_bp.route('/feedback')
@login_required
def feedback():
    feedback_data = []
    courses = Course.query.filter_by(user_id=current_user.id, status='Completed').all()
    for course in courses:
        total_rating = 0
        total_feedback = 0
        comments_count = 0

        for doc in course.documents:
            for feedback in doc.feedbacks:
                if feedback.rating is not None:
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
