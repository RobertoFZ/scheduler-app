from flask import (
    Blueprint, render_template, session, redirect, 
    url_for, flash
)
from functools import wraps

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


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard - requires login"""
    pages = session.get('pages', [])
    return render_template(
        'dashboard.html',
        pages=pages
    ) 