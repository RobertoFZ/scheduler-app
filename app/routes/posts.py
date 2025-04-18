import os
from datetime import datetime
from flask import (
    Blueprint, render_template, request, redirect, 
    url_for, flash, session, current_app
)
from werkzeug.utils import secure_filename
from app.routes.main import login_required
from app.helpers.facebook import schedule_text_post, schedule_photo_post
from app.models import db
from app.models.scheduled_post import ScheduledPost

posts_bp = Blueprint('posts', __name__)


def allowed_file(filename):
    """Check if a file has an allowed extension"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        
        # Find page access token from session
        for page in session.get('pages', []):
            if page['id'] == page_id:
                page_access_token = page['access_token']
                page_name = page['name']
                break
                
        if not page_access_token:
            flash("Invalid page selected", "error")
            return redirect(url_for('posts.create_post'))
            
        # Convert scheduled time to datetime object and Unix timestamp
        try:
            dt = datetime.strptime(scheduled_time, '%Y-%m-%dT%H:%M')
            publish_time = int(dt.timestamp())
        except ValueError:
            flash("Invalid date format", "error")
            return redirect(url_for('posts.create_post'))
        
        # Create post record
        post = ScheduledPost(
            user_id=user_id,
            page_id=page_id,
            page_name=page_name,
            message=message,
            scheduled_time=dt
        )
            
        # Check if file is included
        if 'photo' not in request.files or not request.files['photo'].filename:
            # Text-only post
            result = schedule_text_post(
                page_id, page_access_token, message, publish_time
            )
            
            if result.get('error'):
                post.status = 'failed'
                post.error_message = str(result.get('content'))
                db.session.add(post)
                db.session.commit()
                
                flash(
                    f"Error scheduling post: {result.get('content')}", 
                    "error"
                )
                return redirect(url_for('posts.create_post'))
             
            # Save post record with Facebook post ID    
            post.fb_post_id = result.get('id')
            db.session.add(post)
            db.session.commit()
                
            flash("Post scheduled successfully!", "success")
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
                
                result = schedule_photo_post(
                    page_id, page_access_token, message, 
                    filepath, publish_time
                )
                
                # Clean up the uploaded file
                try:
                    os.remove(filepath)
                except OSError as e:
                    # Ignore cleanup errors
                    print(f"Error removing temp file: {str(e)}")
                
                if result.get('error'):
                    post.status = 'failed'
                    post.error_message = str(result.get('content'))
                    db.session.add(post)
                    db.session.commit()
                    
                    flash(
                        f"Error scheduling post: {result.get('content')}", 
                        "error"
                    )
                    return redirect(url_for('posts.create_post'))
                
                # Save post record with Facebook post ID
                post.fb_post_id = result.get('id')
                db.session.add(post)
                db.session.commit()
                    
                flash("Post with photo scheduled successfully!", "success")
                return redirect(url_for('main.dashboard'))
            else:
                flash(
                    "Invalid file type. Allowed types: png, jpg, jpeg, gif", 
                    "error"
                )
                return redirect(url_for('posts.create_post'))
    
    # GET request - display form
    pages = session.get('pages', [])
    min_date = datetime.now().strftime('%Y-%m-%dT%H:%M')
    return render_template(
        'create_post.html', 
        pages=pages,
        min_date=min_date
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