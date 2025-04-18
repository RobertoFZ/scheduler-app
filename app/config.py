import os

# Facebook API related settings
FB_SCHEDULING_DAYS = int(os.getenv("FB_SCHEDULING_DAYS", 30))
FB_SCHEDULING_MINUTES = int(os.getenv("FB_SCHEDULING_MINUTES", 10))

# Calculate total days to use in the application
# The 10 minutes is converted to a fraction of a day and added to the days
FB_SCHEDULING_LIMIT = (FB_SCHEDULING_DAYS + 
                       (FB_SCHEDULING_MINUTES / (24 * 60)))

# Database settings
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@db:5432/facebook_scheduler"
)

# Facebook App credentials (already in __init__.py, included here for completeness)
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_REDIRECT_URI = os.getenv(
    "FACEBOOK_REDIRECT_URI", 
    "http://localhost:8000/callback"
) 