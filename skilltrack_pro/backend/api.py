from flask import Blueprint, jsonify
from flask_login import login_required
from models import Course, Trainer

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/admin/stats')
@login_required
def admin_stats():
    requested_count = Course.query.filter_by(status='Requested').count()
    in_review_count = Course.query.filter_by(status='In Review').count()
    approved_count = Course.query.filter_by(status='Approved').count()
    rejected_count = Course.query.filter_by(status='Rejected').count()
    completed_count = Course.query.filter_by(status='Completed').count()
    return jsonify({
        'requested': requested_count,
        'in_review': in_review_count,
        'approved': approved_count,
        'rejected': rejected_count,
        'completed': completed_count
    })

@api_bp.route('/admin/courses')
@login_required
def admin_courses():
    courses = Course.query.all()
    course_list = []
    for course in courses:
        trainer_name = None
        if course.trainer_id:
            trainer = Trainer.query.filter_by(id=course.trainer_id).first()
            trainer_name = trainer.name if trainer else None
        
        scheduled_time = None
        if hasattr(course, 'scheduled_time') and course.scheduled_time:
            try:
                scheduled_time = course.scheduled_time.strftime('%Y-%m-%d %H:%M')
            except:
                scheduled_time = str(course.scheduled_time)
        
        course_list.append({
            'id': str(course.id),
            'title': course.title,
            'trainer_name': trainer_name or 'Unassigned',
            'status': course.status,
            'scheduled_time': scheduled_time or '-'
        })
    return jsonify(course_list)
