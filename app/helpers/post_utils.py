from app.helpers.scheduler import update_post_statuses as update_statuses
from app.helpers.scheduler import check_and_schedule_pending_posts


def update_post_statuses():
    """
    Update the status of scheduled posts based on their scheduled time and
    check for posts to schedule within Facebook's limit.
    """
    # Update statuses of existing posts
    updated_count = update_statuses()
    
    # Check for pending posts that need to be scheduled
    check_and_schedule_pending_posts()
    
    return updated_count 