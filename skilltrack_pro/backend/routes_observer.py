from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Documentation, Feedback, Course, Trainer, db
from datetime import datetime

observer_bp = Blueprint('observer', __name__, url_prefix='/observer')

@observer_bp.route('/dashboard')
@login_required
def dashboard():
    # Query documents by status
    pending_docs = Documentation.query.filter_by(status='Pending').all()
    approved_docs = Documentation.query.filter_by(status='Approved').all()
    rejected_docs = Documentation.query.filter_by(status='Rejected').all()

    return render_template(
        'observer_dashboard.html',
        pending_docs=pending_docs,
        approved_docs=approved_docs,
        rejected_docs=rejected_docs
    )

@observer_bp.route('/review/<uuid:doc_id>', methods=['GET', 'POST'])
@login_required
def review_documentation(doc_id):
    doc = Documentation.query.get_or_404(doc_id)
    course = Course.query.get(doc.course_id)
    trainer = Trainer.query.get(course.trainer_id)

    if request.method == 'POST':
        action = request.form.get('action')
        feedback_text = request.form.get('feedback', '').strip()

        if action == 'approve':
            doc.status = 'Approved'
            doc.approved_at = datetime.utcnow()
            # Update course status to Approved
            course.status = 'Approved'
            # Notify admin or relevant party here (TODO)
            flash('Documentation approved successfully.', 'success')

        elif action == 'reject':
            if not feedback_text:
                flash('Please provide feedback when rejecting a document.', 'danger')
                return redirect(url_for('observer.review_documentation', doc_id=doc_id))

            doc.status = 'Rejected'
            doc.rejected_at = datetime.utcnow()
            # Update course status back to Requested so trainer can see it
            course.status = 'Requested'
            # Save feedback linked to this doc
            feedback = Feedback(
                documentation_id=doc.id,
                comments=feedback_text,
                created_at=datetime.utcnow()
            )
            db.session.add(feedback)
            # Notify trainer with feedback (TODO)
            flash('Documentation rejected and feedback has been recorded.', 'warning')

        # Track revision cycles
        doc.revision_number = (doc.revision_number or 0) + 1

        db.session.commit()
        return redirect(url_for('observer.dashboard'))

    # On GET - show review page with document info
    feedbacks = Feedback.query.filter_by(documentation_id=doc.id).order_by(Feedback.created_at.desc()).all()

    return render_template(
        'review_documentation.html',
        doc=doc,
        course=course,
        trainer=trainer,
        feedbacks=feedbacks
    )

@observer_bp.route('/pending_reviews')
@login_required
def pending_reviews():
    pending_docs = Documentation.query.filter_by(status='Pending').all()
    return render_template('pending_reviews.html', pending_docs=pending_docs)


@observer_bp.route('/completed_reviews')
@login_required
def completed_reviews():
    # Show approved documents as completed reviews
    completed_docs = Documentation.query.filter_by(status='Approved').all()
    return render_template('completed_reviews.html', completed_docs=completed_docs)

