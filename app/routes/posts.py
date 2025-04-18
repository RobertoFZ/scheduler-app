import os
import json
from datetime import datetime, timedelta
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, session, current_app
)
from werkzeug.utils import secure_filename
from app.routes.main import login_required
from app.helpers.facebook import schedule_text_post, schedule_photo_post
from app.models import db
from app.models.scheduled_post import ScheduledPost
import logging
from app.config import FB_SCHEDULING_LIMIT

posts_bp = Blueprint('posts', __name__)

logger = logging.getLogger(__name__)


def allowed_file(filename):
    """Check if a file has an allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def format_fb_error(error_content):
    """Format Facebook API error into a readable message"""
    if isinstance(error_content, str):
        try:
            # Try to parse string as JSON
            error_content = json.loads(error_content)
        except json.JSONDecodeError:
            return error_content
    
    if isinstance(error_content, dict):
        if 'message' in error_content:
            if 'error_user_title' in error_content:
                return (f"{error_content.get('error_user_title')}: "
                        f"{error_content.get('message')}")
            return error_content.get('message')
        elif 'error' in error_content and isinstance(
                error_content['error'], dict):
            error_obj = error_content['error']
            if 'message' in error_obj:
                return (f"Error {error_obj.get('code', '')}: "
                        f"{error_obj.get('message')}")
    
    # Fallback to string representation
    return str(error_content)


@posts_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    """Create new post form and submission handling"""
    # Ensure user_id is available
    user_id = session.get('user_id')
    if not user_id:
        flash("Session incomplete. Please log out and log back in.", "error")
        return redirect(url_for('auth.logout'))
        
    if request.method == 'POST':
        # Get form data
        page_id = request.form.get('page_id')
        page_name = None
        page_access_token = None
        message = request.form.get('message')
        scheduled_time = request.form.get('scheduled_time')
        
        # Store form data in session for restoration on error
        session['post_form_data'] = {
            'page_id': page_id,
            'message': message,
            'scheduled_time': scheduled_time
        }
        
        # Find page access token from session
        for page in session.get('pages', []):
            if page['id'] == page_id:
                page_access_token = page['access_token']
                page_name = page['name']
                break
                
        if not page_access_token:
            flash(
                "Invalid page selected. Please choose a valid Facebook page.", 
                "error"
            )
            return redirect(url_for('posts.create_post'))
        
        # Validate message is not empty
        if not message or message.strip() == '':
            flash("Post message cannot be empty.", "error")
            return redirect(url_for('posts.create_post'))
            
        # Convert scheduled time to datetime object and Unix timestamp
        try:
            dt = datetime.strptime(scheduled_time, '%Y-%m-%dT%H:%M')
            publish_time = int(dt.timestamp())
            
            # Ensure scheduled time is in the future
            if dt <= datetime.now():
                flash("Scheduled time must be in the future.", "error")
                return redirect(url_for('posts.create_post'))
                
        except ValueError:
            flash(
                "Invalid date format. Please use the date picker to select "
                "a valid date and time.", 
                "error"
            )
            return redirect(url_for('posts.create_post'))
        
        # Check if the scheduled time is within Facebook's scheduling limit
        now = datetime.now()
        fb_limit_date = now + timedelta(days=FB_SCHEDULING_LIMIT)
        within_fb_limit = dt <= fb_limit_date
        
        # Create post record - always save to our database first
        post = ScheduledPost(
            user_id=user_id,
            page_id=page_id,
            page_name=page_name,
            message=message,
            scheduled_time=dt,
            page_access_token=page_access_token,
            status='pending' if not within_fb_limit else 'scheduled'
        )
            
        # Check if file is included
        if 'photo' not in request.files or not request.files['photo'].filename:
            # Text-only post
            if within_fb_limit:
                # If within Facebook's limit, schedule immediately
                result = schedule_text_post(
                    page_id, page_access_token, message, publish_time
                )
                
                if result.get('error'):
                    error_message = format_fb_error(result.get('content'))
                    flash(
                        f"Facebook API Error: {error_message}. "
                        f"Please try again.", 
                        "error"
                    )
                    return redirect(url_for('posts.create_post'))
                
                # Save post record with Facebook post ID
                post.fb_post_id = result.get('id')
                post.submitted_to_facebook = True
                post.last_submission_attempt = now
                flash("Post scheduled successfully on Facebook!", "success")
                db.session.add(post)
                db.session.commit()
            else:
                # Beyond Facebook's limit, save for later scheduling
                flash(
                    "Post saved for future scheduling "
                    f"(beyond Facebook's {FB_SCHEDULING_LIMIT:.1f} "
                    f"day limit).", 
                    "success"
                )
                db.session.add(post)
                db.session.commit()
            
            return redirect(url_for('main.dashboard'))
        else:
            # Photo post
            file = request.files['photo']
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                upload_folder = os.path.join(current_app.root_path, 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                
                # Update post record
                post.has_image = True
                post.image_path = filepath
                
                if within_fb_limit:
                    # If within Facebook's limit, schedule immediately
                    result = schedule_photo_post(
                        page_id, page_access_token, message, 
                        filepath, publish_time
                    )
                    
                    # Clean up the uploaded file
                    try:
                        os.remove(filepath)
                    except OSError as e:
                        # Log cleanup errors but don't affect user flow
                        logger.warning(f"Error removing temp file: {str(e)}")
                    
                    if result.get('error'):
                        error_message = format_fb_error(result.get('content'))
                        flash(
                            f"Facebook API Error: {error_message}. "
                            f"Please try again.", 
                            "error"
                        )
                        return redirect(url_for('posts.create_post'))
                    
                    # Save post record with Facebook post ID
                    post.fb_post_id = result.get('id')
                    post.submitted_to_facebook = True
                    post.last_submission_attempt = now
                    flash(
                        "Post with photo scheduled successfully on Facebook!", 
                        "success"
                    )
                    db.session.add(post)
                    db.session.commit()
                else:
                    # Beyond Facebook's limit, save for later scheduling
                    # For posts with images, we need to save the image
                    permanent_path = f"{upload_folder}/post_{filename}"
                    os.rename(filepath, permanent_path)
                    post.image_path = permanent_path
                    flash(
                        "Post with photo saved for future scheduling "
                        f"(beyond Facebook's {FB_SCHEDULING_LIMIT:.1f} "
                        f"day limit).", 
                        "success"
                    )
                    db.session.add(post)
                    db.session.commit()
                
                return redirect(url_for('main.dashboard'))
            else:
                flash(
                    "Invalid file type. Allowed types: png, jpg, jpeg, gif. "
                    "Please select a valid image file.", 
                    "error"
                )
                return redirect(url_for('posts.create_post'))
    
    # GET request - display form
    pages = session.get('pages', [])
    min_date = datetime.now().strftime('%Y-%m-%dT%H:%M')
    
    # Restore form data if available
    form_data = session.pop('post_form_data', None)
    
    return render_template(
        'create_post.html', 
        pages=pages,
        min_date=min_date,
        form_data=form_data
    )


@posts_bp.route('/list', methods=['GET'])
@login_required
def list_posts():
    """List all scheduled posts for the current user with pagination"""
    # Ensure user_id is available
    user_id = session.get('user_id')
    if not user_id:
        flash("Session incomplete. Please log out and log back in.", "error")
        return redirect(url_for('auth.logout'))
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 6  # Show 6 posts per page (2 rows of 3 in desktop view)
    
    # Get paginated posts
    pagination = ScheduledPost.query.filter_by(
        user_id=user_id
    ).order_by(
        ScheduledPost.scheduled_time.desc()
    ).paginate(
        page=page, 
        per_page=per_page,
        error_out=False
    )
    
    posts = pagination.items
    
    return render_template(
        'list_posts.html', 
        posts=posts, 
        pagination=pagination
    )


@posts_bp.route('/details/<int:post_id>', methods=['GET'])
@login_required
def post_details(post_id):
    """Show details for a specific post"""
    # Ensure user_id is available
    user_id = session.get('user_id')
    if not user_id:
        flash("Session incomplete. Please log out and log back in.", "error")
        return redirect(url_for('auth.logout'))
        
    post = ScheduledPost.query.get_or_404(post_id)
    
    # Make sure the user can only view their own posts
    if post.user_id != user_id:
        flash("You don't have permission to view this post", "error")
        return redirect(url_for('posts.list_posts'))
        
    return render_template('post_details.html', post=post) 