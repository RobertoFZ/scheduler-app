import os
from app import create_app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Get port from environment variable (for Render.com compatibility)
    port = int(os.getenv("PORT", 8000))
    # Run the application based on environment
    debug_mode = os.getenv("FLASK_ENV", "production") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug_mode) 