from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from models import Course, Trainer, Feedback, Documentation, db
from werkzeug.utils import secure_filename
from sqlalchemy import or_
import os

trainer_bp = Blueprint('trainer', __name__, url_prefix='/trainer')

# Helper: Allowed file extensions for documentation upload
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'ppt', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper: get or create the Trainer record for the logged-in user
def get_or_create_current_trainer():
    trainer = Trainer.query.filter_by(user_id=current_user.id).first()
    if not trainer:
        # Auto-provision a trainer profile so flows work end-to-end
        default_name = getattr(current_user, 'username', None) or (getattr(current_user, 'email', '') or 'Trainer').split('@')[0]
        trainer = Trainer(name=default_name, user_id=current_user.id, status='Active')
        db.session.add(trainer)
        db.session.commit()
    return trainer

@trainer_bp.route('/dashboard')
@login_required
def dashboard():
    trainer = get_or_create_current_trainer()
    requested_count = Course.query.filter(
        (Course.trainer_id == None) | (Course.trainer_id == trainer.id),
        Course.status == 'Requested'
    ).count()
    in_review_count = Course.query.filter_by(trainer_id=trainer.id, status='In Review').count()
    approved_count = Course.query.filter_by(trainer_id=trainer.id, status='Approved').count()
    completed_count = Course.query.filter_by(trainer_id=trainer.id, status='Completed').count()
    rejected_count = Course.query.filter_by(trainer_id=trainer.id, status='Rejected').count()

    return render_template(
        'trainer_dashboard.html',
        requested_count=requested_count,
        in_review_count=in_review_count,
        approved_count=approved_count,
        completed_count=completed_count,
        rejected_count=rejected_count,
    )

@trainer_bp.route('/my_courses')
@login_required
def my_courses():
    trainer = get_or_create_current_trainer()
    courses = Course.query.filter_by(trainer_id=trainer.id).all()
    return render_template('trainer_my_courses.html', courses=courses)

@trainer_bp.route('/course_requests')
@login_required
def course_requests():
    # Show requests assigned or unassigned (trainer_id is None) for current trainer
    trainer = get_or_create_current_trainer()
    # Also include requests pre-assigned by admin to a trainer record that
    # matches this trainer's name (admin-owned trainer rows)
    # Also include rejected courses that need to be fixed
    requests = (
        Course.query
        .filter(
            or_(
                Course.status == 'Requested',
                Course.status == 'Rejected'  # Show rejected courses so trainer can fix them
            ),
            or_(
                Course.trainer_id == None,
                Course.trainer_id == trainer.id,
                Course.trainer.has(Trainer.name.ilike(trainer.name))
            )
        )
        .all()
    )
    return render_template('trainer_course_requests.html', requests=requests)

@trainer_bp.route('/course_requests/<course_id>/accept', methods=['POST'])
@login_required
def accept_course_request(course_id):
    trainer = get_or_create_current_trainer()
    course = Course.query.filter_by(id=course_id, status='Requested').first_or_404()
    course.trainer_id = trainer.id
    course.status = 'In Review'
    
    # Create initial documentation record for the course
    initial_doc = Documentation(
        course_id=course_id,
        file_path='',  # Will be set when file is uploaded
        status='Pending',
        revision_number=1
    )
    db.session.add(initial_doc)
    
    db.session.commit()
    flash('Course request accepted and moved to In Review.', 'success')
    return redirect(url_for('trainer.course_requests'))

@trainer_bp.route('/course_requests/<course_id>/decline', methods=['POST'])
@login_required
def decline_course_request(course_id):
    course = Course.query.filter_by(id=course_id, status='Requested').first_or_404()
    course.trainer_id = None
    # Optionally, add a declined status or keep as Requested for reassignment
    db.session.commit()
    flash('Course request declined.', 'info')
    return redirect(url_for('trainer.course_requests'))

@trainer_bp.route('/upload_documentation/<course_id>', methods=['GET', 'POST'])
@login_required
def upload_documentation(course_id):
    trainer = get_or_create_current_trainer()
    course = Course.query.filter_by(id=course_id, trainer_id=trainer.id).first_or_404()

    # Find the latest documentation entry for display
    latest_doc = (
        Documentation.query
        .filter_by(course_id=course.id)
        .order_by(Documentation.submitted_at.desc())
        .first()
    )

    if request.method == 'POST':
        if 'documentation' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['documentation']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Save under static so observer link can serve via url_for('static', ...)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'docs', str(course.id))
            os.makedirs(upload_folder, exist_ok=True)
            abs_path = os.path.join(upload_folder, filename)
            file.save(abs_path)

            # Store path relative to static/
            relative_path = os.path.join('uploads', 'docs', str(course.id), filename).replace('\\', '/')

            # Determine next revision number
            next_revision = (latest_doc.revision_number if latest_doc else 0) + 1

            new_doc = Documentation(
                course_id=course.id,
                file_path=relative_path,
                status='Pending',
                revision_number=next_revision,
            )
            db.session.add(new_doc)
            db.session.commit()

            flash('Documentation uploaded and set to Pending for review.', 'success')
            return redirect(url_for('trainer.upload_documentation', course_id=course_id))
        else:
            flash('File type not allowed.', 'danger')

    return render_template('trainer_upload_documentation.html', course=course, latest_doc=latest_doc)

@trainer_bp.route('/submit_for_review/<course_id>', methods=['POST'])
@login_required
def submit_for_review(course_id):
    trainer = get_or_create_current_trainer()
    course = Course.query.filter_by(id=course_id, trainer_id=trainer.id).first_or_404()
    
    # If course was rejected, update its status back to In Review
    if course.status == 'Rejected':
        course.status = 'In Review'
    
    # Ensure the latest doc is marked Pending (queue for observer)
    latest_doc = (
        Documentation.query
        .filter_by(course_id=course.id)
        .order_by(Documentation.submitted_at.desc())
        .first()
    )
    if latest_doc:
        latest_doc.status = 'Pending'
        db.session.commit()
        flash('Documentation submitted for observer review.', 'success')
    else:
        flash('No documentation found to submit.', 'danger')
    
    return redirect(url_for('trainer.upload_documentation', course_id=course_id))

@trainer_bp.route('/approvals_feedback')
@login_required
def approvals_feedback():
    trainer = get_or_create_current_trainer()
    courses = Course.query.filter_by(trainer_id=trainer.id).filter(
        Course.status.in_(['In Review', 'Approved'])
    ).all()
    return render_template('trainer_approvals_feedback.html', courses=courses)

@trainer_bp.route('/feedback/<uuid:course_id>', methods=['GET', 'POST'])
@login_required
def provide_feedback(course_id):
    trainer = get_or_create_current_trainer()
    course = Course.query.filter_by(id=course_id, trainer_id=trainer.id).first_or_404()

    if request.method == 'POST':
        comments = request.form.get('comments')
        rating = request.form.get('rating')
        
        # Get the latest documentation for this course
        latest_doc = Documentation.query.filter_by(course_id=course.id).order_by(Documentation.revision_number.desc()).first()
        if latest_doc:
            feedback = Feedback(documentation_id=latest_doc.id, comments=comments, rating=rating)
            db.session.add(feedback)
            db.session.commit()
            flash('Feedback submitted.', 'success')
        else:
            flash('No documentation found for this course.', 'danger')
        return redirect(url_for('trainer.approvals_feedback'))

    # Get feedbacks from all documentations for this course
    existing_feedbacks = []
    docs = Documentation.query.filter_by(course_id=course.id).all()
    for doc in docs:
        doc_feedbacks = Feedback.query.filter_by(documentation_id=doc.id).all()
        existing_feedbacks.extend(doc_feedbacks)
    
    return render_template('trainer_feedback.html', course=course, feedbacks=existing_feedbacks)

@trainer_bp.route('/completed_sessions')
@login_required
def completed_sessions():
    trainer = get_or_create_current_trainer()
    courses = Course.query.filter_by(trainer_id=trainer.id, status='Completed').all()
    return render_template('trainer_completed_sessions.html', courses=courses)

@trainer_bp.route('/completed_sessions/<uuid:course_id>/report', methods=['GET', 'POST'])
@login_required
def session_report(course_id):
    trainer = get_or_create_current_trainer()
    course = Course.query.filter_by(id=course_id, trainer_id=trainer.id, status='Completed').first_or_404()

    if request.method == 'POST':
        report = request.form.get('report')
        course.completion_report = report
        db.session.commit()
        flash('Session report submitted.', 'success')
        return redirect(url_for('trainer.completed_sessions'))

    return render_template('trainer_session_report.html', course=course)
