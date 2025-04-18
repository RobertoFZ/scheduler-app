import os
import json
from datetime import datetime, timedelta
from app.models import db
from app.models.scheduled_post import ScheduledPost
from app.helpers.facebook import schedule_text_post, schedule_photo_post
import logging
from app.config import FB_SCHEDULING_LIMIT

logger = logging.getLogger(__name__)


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


def check_and_schedule_pending_posts():
    """
    Check for posts that are ready to be scheduled on Facebook.
    
    We look for posts that:
    1. Are not yet submitted to Facebook
    2. Have a scheduled time that's within Facebook's 
       scheduling limit (28 days)
    3. Have a status of 'pending'
    """
    now = datetime.utcnow()
    fb_limit_date = now + timedelta(days=FB_SCHEDULING_LIMIT)
    
    # Find posts that need to be scheduled
    pending_posts = ScheduledPost.query.filter(
        ScheduledPost.submitted_to_facebook.is_(False),
        ScheduledPost.status == 'pending',
        ScheduledPost.scheduled_time <= fb_limit_date
    ).all()
    
    if not pending_posts:
        logger.info("No pending posts to schedule")
        return True, "No pending posts to schedule"
    
    logger.info(f"Found {len(pending_posts)} pending posts to schedule")
    
    for post in pending_posts:
        try:
            # Attempt to schedule the post on Facebook
            success = schedule_post_on_facebook(post)
            if not success:
                logger.info(
                    f"Failed to schedule post {post.id}, will retry later"
                )
        except Exception as e:
            logger.error(
                f"Error scheduling post {post.id}: "
                f"{str(e)}"
            )
            # Don't update the post, so it can be retried later


def schedule_post_on_facebook(post):
    """Schedule a single post on Facebook"""
    now = datetime.utcnow()
    
    # Get Unix timestamp for scheduled time
    publish_time = int(post.scheduled_time.timestamp())
    
    try:
        if post.has_image and post.image_path:
            # Schedule a post with photo
            if os.path.exists(post.image_path):
                result = schedule_photo_post(
                    post.page_id,
                    post.page_access_token,
                    post.message,
                    post.image_path,
                    publish_time
                )
            else:
                # Image file is missing
                raise FileNotFoundError(
                    f"Image file not found: {post.image_path}"
                )
        else:
            # Schedule a text-only post
            result = schedule_text_post(
                post.page_id,
                post.page_access_token,
                post.message,
                publish_time
            )
        
        # Check if there was an error
        if result.get('error'):
            error_message = format_fb_error(result.get('content'))
            logger.error(
                f"Failed to schedule post {post.id}: {error_message}"
            )
            # Don't update the post status, so it can be retried later
            return False
        else:
            # Success! Update post status
            post.status = 'scheduled'
            post.submitted_to_facebook = True
            post.fb_post_id = result.get('id')
            post.last_submission_attempt = now
            post.error_message = None
            logger.info(
                f"Successfully scheduled post {post.id} on Facebook"
            )
            
            # Clean up image file if it was a photo post
            if (post.has_image and post.image_path and 
                    os.path.exists(post.image_path)):
                try:
                    os.remove(post.image_path)
                    post.image_path = None
                except OSError as e:
                    logger.warning(
                        f"Failed to remove image file: {str(e)}"
                    )
            
            # Save changes
            db.session.commit()
            return True
    
    except Exception as e:
        # Log error but don't update the post
        logger.exception(f"Exception scheduling post {post.id}: {str(e)}")
        return False


def update_post_statuses():
    """
    Update the status of scheduled posts based on their scheduled time.
    Posts with scheduled_time in the past should be marked as 'published'
    if they have a valid fb_post_id.
    """
    now = datetime.utcnow()
    
    # Get all scheduled posts with scheduled_time in the past
    posts_to_update = ScheduledPost.query.filter(
        ScheduledPost.status == 'scheduled',
        ScheduledPost.scheduled_time <= now
    ).all()
    
    updated_count = 0
    for post in posts_to_update:
        if post.fb_post_id:
            post.status = 'published'
            post.published = True
            updated_count += 1
    
    if updated_count > 0:
        db.session.commit()
        logger.info(f"Marked {updated_count} posts as published")
        
    return updated_count 