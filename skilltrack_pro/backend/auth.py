from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from flask_login import login_user, logout_user, login_required
from .supabase_client import supabase
from .models import User, db

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

        # Find or create user in local DB
        user = User.query.filter_by(email=email).first()
        if not user:
            username = request.form.get('username')
            username = email.split('@')[0]
            user = User(email=email, supabase_user_id=user_data.id, role=role,username=username )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

        login_user(user)  # Log user in with Flask-Login

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

    # GET request - render login form
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('auth.login'))

