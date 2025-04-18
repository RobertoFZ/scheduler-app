from datetime import datetime
from app.models import db


class ScheduledPost(db.Model):
    """Model for storing scheduled Facebook posts"""
    
    __tablename__ = 'scheduled_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), nullable=False)  # Facebook user ID
    page_id = db.Column(db.String(255), nullable=False)  # Facebook page ID
    page_name = db.Column(db.String(255), nullable=False)  # Facebook page name
    message = db.Column(db.Text, nullable=True)  # Post content
    has_image = db.Column(db.Boolean, default=False)  # Whether the post includes an image
    image_path = db.Column(db.String(255), nullable=True)  # Local path to image if any
    scheduled_time = db.Column(db.DateTime, nullable=False)  # When to publish
    published = db.Column(db.Boolean, default=False)  # Whether post was published
    fb_post_id = db.Column(db.String(255), nullable=True)  # Facebook post ID after publishing
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='scheduled')  # scheduled, published, failed, pending
    error_message = db.Column(db.Text, nullable=True)  # Error message if post failed
    submitted_to_facebook = db.Column(db.Boolean, default=False)  # Whether the post has been submitted to Facebook
    last_submission_attempt = db.Column(db.DateTime, nullable=True)  # Last time we tried to submit to Facebook
    page_access_token = db.Column(db.Text, nullable=True)  # Stored page access token for scheduling
    
    def __repr__(self):
        return f'<ScheduledPost {self.id}: {self.page_name} @ {self.scheduled_time}>'
    
    def to_dict(self):
        """Convert post to dictionary for API responses"""
        return {
            'id': self.id,
            'page_id': self.page_id,
            'page_name': self.page_name,
            'message': self.message,
            'has_image': self.has_image,
            'scheduled_time': self.scheduled_time.isoformat(),
            'published': self.published,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'fb_post_id': self.fb_post_id,
            'submitted_to_facebook': self.submitted_to_facebook
        } 