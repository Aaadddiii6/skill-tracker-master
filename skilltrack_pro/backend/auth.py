from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, login_required
from .supabase_client import supabase, register_user
from .models import User, db
import logging

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
        except Exception as e:
            flash(f"Error connecting to Supabase: {e}", "danger")
            return render_template('login.html')

        user_data = response.user
        if not user_data:
            flash("Invalid credentials", "danger")
            return render_template('login.html')

        role = user_data.user_metadata.get('role', None)
        if not role:
            flash("No role assigned to this account", "danger")
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()
        if not user:
            username = email.split('@')
            user = User(email=email, supabase_user_id=user_data.id, role=role, username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        session['role'] = role

        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'trainer':
            return redirect(url_for('trainer.dashboard'))
        elif role == 'observer':
            return redirect(url_for('observer.dashboard'))
        else:
            flash("Invalid role assigned", "danger")
            logout_user()
            return redirect(url_for('auth.login'))

    return render_template('login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        logging.debug(f"Received registration POST with form data: {request.form}")
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        # Validate role
        if role not in ['trainer', 'observer']:
            flash("Invalid role selected", "danger")
            return render_template('register.html')

        result = register_user(email, password, username, role)

        if 'error' in result and result['error']:
            flash(result['error'], 'danger')
            return render_template('register.html')

        # On success: result contains keys 'message' and 'user'
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, username=username, role=role, supabase_user_id=result['user'].id)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

        login_user(user)
        flash("Registration successful! Welcome.", "success")

        if role == 'trainer':
            return redirect(url_for('trainer.dashboard'))
        else:
            return redirect(url_for('observer.dashboard'))

    # GET or fallback
    return render_template('register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('auth.login'))
