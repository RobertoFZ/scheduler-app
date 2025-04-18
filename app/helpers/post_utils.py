from datetime import datetime
from app.models import db
from app.models.scheduled_post import ScheduledPost


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
        
    return updated_count 