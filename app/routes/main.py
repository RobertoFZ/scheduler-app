from flask import (
    Blueprint, render_template, session, redirect, 
    url_for, flash
)
from functools import wraps
from app.helpers.post_utils import update_post_statuses
from app.models.scheduled_post import ScheduledPost
from datetime import datetime

main_bp = Blueprint('main', __name__)


def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'access_token' not in session:
            flash("Please log in to access this page", "error")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@main_bp.route('/')
def index():
    """Homepage"""
    print("DEBUG: Index route accessed - hot reload is working!")
    logged_in = 'access_token' in session
    return render_template('index.html', logged_in=logged_in)


@main_bp.route('/privacy-policy')
def privacy_policy():
    """Privacy Policy page for Facebook app validation"""
    now = datetime.now()
    return render_template('privacy_policy.html', now=now)


@main_bp.route('/terms-of-service')
def terms_of_service():
    """Terms of Service page for Facebook app validation"""
    now = datetime.now()
    return render_template('terms_of_service.html', now=now)


@main_bp.route('/data-deletion')
def data_deletion():
    """Data Deletion Instructions page for Facebook app validation"""
    now = datetime.now()
    return render_template('data_deletion.html', now=now)


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - requires login"""
    # Ensure user_id is available
    user_id = session.get('user_id')
    if not user_id:
        flash("Session incomplete. Please log out and log back in.", "error")
        return redirect(url_for('auth.logout'))
        
    # Update post statuses
    updated_count = update_post_statuses()
    if updated_count > 0:
        message = f"{updated_count} posts have been marked as published"
        flash(message, "success")
    
    # Get the user's pages
    pages = session.get('pages', [])
    
    # Get recent posts (limit to 6 - same as one page of full list)
    recent_posts = ScheduledPost.query.filter_by(
        user_id=user_id
    ).order_by(
        ScheduledPost.scheduled_time.desc()
    ).limit(6).all()
    
    return render_template(
        'dashboard.html',
        pages=pages,
        recent_posts=recent_posts
    )


@main_bp.route('/account-settings')
@login_required
def account_settings():
    """Account settings page - requires login"""
    # Ensure user_id is available
    user_id = session.get('user_id')
    if not user_id:
        flash("Session incomplete. Please log out and log back in.", "error")
        return redirect(url_for('auth.logout'))
    
    return render_template('account_settings.html') 