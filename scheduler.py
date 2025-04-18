import os
import time
import logging
from logging.handlers import RotatingFileHandler
import sys
from dotenv import load_dotenv

# Load environment variables before creating the app
load_dotenv()

# Configure logging
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'scheduler.log')

logger = logging.getLogger('scheduler')
logger.setLevel(logging.INFO)

# Add rotating file handler
file_handler = RotatingFileHandler(
    log_file, maxBytes=5*1024*1024, backupCount=5
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Add console handler for development
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
console_handler.setLevel(logging.INFO)
logger.addHandler(console_handler)

# Import app after logging is configured
from app import create_app
from app.helpers.scheduler import check_and_schedule_pending_posts, update_post_statuses

app = create_app()

def run_scheduler():
    """Run the scheduler to check and process pending posts"""
    with app.app_context():
        logger.info("Scheduler started")
        try:
            # Update posts that have been published
            count = update_post_statuses()
            logger.info(f"Updated status for {count} posts")
            
            # Check and schedule pending posts
            check_and_schedule_pending_posts()
            
            logger.info("Scheduler completed successfully")
        except Exception as e:
            logger.exception(f"Error in scheduler: {str(e)}")


if __name__ == '__main__':
    # Check if the --loop flag is set
    loop_mode = '--loop' in sys.argv
    interval = 3600  # 1 hour in seconds
    
    # Check for custom interval
    for arg in sys.argv:
        if arg.startswith('--interval='):
            try:
                interval = int(arg.split('=')[1])
            except (ValueError, IndexError):
                pass
    
    with app.app_context():
        if loop_mode:
            logger.info(f"Starting scheduler in loop mode (interval: {interval} seconds)")
            while True:
                try:
                    run_scheduler()
                except Exception as e:
                    logger.exception(f"Unhandled error in scheduler loop: {str(e)}")
                
                logger.info(f"Scheduler sleeping for {interval} seconds")
                time.sleep(interval)
        else:
            logger.info("Running scheduler once")
            run_scheduler() 