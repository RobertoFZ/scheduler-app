from flask import (
    Blueprint, redirect, request, session, 
    url_for, flash, current_app
)
from app.helpers.auth import (
    exchange_token, get_long_lived_token, get_user_pages, get_user_info
)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login')
def login():
    """Redirect to Facebook OAuth page"""
    app_id = current_app.config['APP_ID']
    redirect_uri = current_app.config['REDIRECT_URI']
    scope = "pages_manage_posts,pages_read_engagement,pages_show_list"
    print(f"App ID: {app_id}")
    print(f"Redirect URI: {redirect_uri}")

    auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth?"
        f"client_id={app_id}&redirect_uri={redirect_uri}&scope={scope}"
    )
    return redirect(auth_url)


@auth_bp.route('/callback')
def callback():
    """Handle OAuth callback from Facebook"""
    error = request.args.get('error')
    if error:
        flash(f"Authorization failed: {error}", "error")
        return redirect(url_for('main.index'))
        
    # Exchange code for token
    try:
        code = request.args.get('code')
        short_lived_token = exchange_token(code)
        
        # Exchange short-lived token for long-lived token
        token_data = get_long_lived_token(short_lived_token)
        access_token = token_data['access_token']
        
        # Get user information
        user_info = get_user_info(access_token)
        
        # Store token and user info in session
        session.permanent = True
        session['access_token'] = access_token
        session['expires_at'] = token_data['expires_at']
        session['user_id'] = user_info['id']
        session['user_name'] = user_info.get('name', '')
        
        # Get pages user has access to
        pages = get_user_pages(access_token)
        if not pages:
            flash(
                "No Facebook Pages found. "
                "Please create a page or get access to one.",
                "error"
            )
            return redirect(url_for('main.index'))
            
        # Store pages in session
        session['pages'] = pages
        
        flash("Successfully logged in with Facebook", "success")
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        flash(f"Error during authentication: {str(e)}", "error")
        return redirect(url_for('main.index'))


@auth_bp.route('/logout')
def logout():
    """Log out user by clearing session"""
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for('main.index')) 