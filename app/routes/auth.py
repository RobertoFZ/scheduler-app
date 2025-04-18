from flask import (
    Blueprint, redirect, request, session, 
    url_for, flash, current_app, jsonify
)
from app.helpers.auth import (
    exchange_token, get_long_lived_token, get_user_pages, get_user_info
)
from app.helpers.user_data import delete_user_data

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login')
def login():
    """Redirect to Facebook OAuth page"""
    app_id = current_app.config['APP_ID']
    redirect_uri = current_app.config['REDIRECT_URI']
    scope = "email,pages_manage_posts,pages_read_engagement,pages_show_list"

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
        
        # Store email if available
        if 'email' in user_info:
            session['user_email'] = user_info['email']
        
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


@auth_bp.route('/delete-account', methods=['POST'])
def delete_account():
    """Delete user account and all associated data"""
    user_id = session.get('user_id')
    if not user_id:
        flash("You must be logged in to delete your account", "error")
        return redirect(url_for('main.index'))
    
    # Delete user data
    success = delete_user_data(user_id)
    
    if success:
        # Clear session
        session.clear()
        flash("Your account and all associated data have been deleted", "success")
    else:
        flash("There was an error deleting your account. Please try again or contact support.", "error")
    
    return redirect(url_for('main.index'))


@auth_bp.route('/facebook-deletion-callback', methods=['GET', 'POST'])
def facebook_deletion_callback():
    """
    Handle Facebook's Data Deletion Callback API
    Documentation: 
    https://developers.facebook.com/docs/development/create-an-app/app-dashboard/data-deletion-callback
    """
    if request.method == 'GET':
        # Facebook requires a GET response with confirmation_code
        confirmation_code = request.args.get('confirmation_code')
        if confirmation_code:
            return confirmation_code
        return "Please provide a confirmation code", 400
    
    elif request.method == 'POST':
        try:
            # Get the request payload
            data = request.json
            user_id = data.get('user_id')
            
            if not user_id:
                return jsonify({
                    "url": request.url,
                    "error": {
                        "message": "Missing user_id parameter",
                        "code": 100
                    }
                }), 400
            
            # Delete user data using the helper function
            success = delete_user_data(user_id)
            
            if not success:
                return jsonify({
                    "url": request.url,
                    "error": {
                        "message": "Data deletion failed",
                        "code": 200
                    }
                }), 500
            
            # Return confirmation to Facebook
            return jsonify({
                "url": request.url,
                "confirmation_code": data.get('confirmation_code'),
                "status": "success"
            })
            
        except Exception as e:
            # Return error to Facebook
            return jsonify({
                "url": request.url,
                "error": {
                    "message": str(e),
                    "code": 500
                }
            }), 500 