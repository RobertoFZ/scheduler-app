import os
from app import create_app
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # Run the application based on environment
    debug_mode = os.getenv("FLASK_ENV", "production") != "production"
    app.run(host="0.0.0.0", port=8000, debug=debug_mode) 