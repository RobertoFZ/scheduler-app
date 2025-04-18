import os
import logging
from app.models import db
from app.models.scheduled_post import ScheduledPost

logger = logging.getLogger(__name__)

def delete_user_data(user_id):
    """
    Delete all data associated with a user
    
    Args:
        user_id (str): Facebook user ID
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get all user's scheduled posts
        posts = ScheduledPost.query.filter_by(user_id=user_id).all()
        
        # Delete associated files first
        for post in posts:
            if post.has_image and post.image_path and os.path.exists(post.image_path):
                try:
                    os.remove(post.image_path)
                    logger.info(f"Deleted image file: {post.image_path}")
                except OSError as e:
                    logger.error(f"Error deleting file {post.image_path}: {str(e)}")
        
        # Delete all posts from database
        deletion_count = ScheduledPost.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        
        logger.info(f"Deleted {deletion_count} posts for user {user_id}")
        return True
        
    except Exception as e:
        db.session.rollback()
        logger.exception(f"Error deleting user data for {user_id}: {str(e)}")
        return False 