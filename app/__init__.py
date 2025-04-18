import os
from flask import Flask
from flask_session import Session
from app.models import db


def create_app(test_config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__, instance_relative_config=True)
    print(os.getenv("FACEBOOK_APP_ID"))
    # Default configuration
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "facebook-scheduler-secret-key"),
        SESSION_TYPE='filesystem',
        SESSION_FILE_DIR='flask_session',
        # Map FACEBOOK_ prefixed env vars to the config keys used in the app
        APP_ID=os.getenv("FACEBOOK_APP_ID"),
        APP_SECRET=os.getenv("FACEBOOK_APP_SECRET"),
        REDIRECT_URI=os.getenv("FACEBOOK_REDIRECT_URI"),
        PERMANENT_SESSION_LIFETIME=60 * 24 * 60 * 60,  # 60 days in seconds
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "postgresql://postgres:postgres@db:5432/facebook_scheduler"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    # Ensure the upload folder exists
    os.makedirs(os.path.join(app.root_path, 'uploads'), exist_ok=True)
    os.makedirs('flask_session', exist_ok=True)
    
    # Initialize session extension
    Session(app)
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.auth import auth_bp
    from app.routes.posts import posts_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(posts_bp, url_prefix='/posts')
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Return the configured app
    return app 