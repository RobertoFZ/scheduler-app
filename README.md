# Facebook Post Scheduler

A Flask application that allows you to schedule Facebook posts with text and optional images.

## Features

- Facebook OAuth authentication
- Schedule posts to your Facebook pages
- Support for text-only or image posts
- User-friendly interface with date and time picker
- Responsive design for mobile and desktop
- Containerized with Docker for easy deployment
- Modular code organization with Flask Blueprints

## Project Structure

```
facebook_scheduler/
├── app/                    # Application package
│   ├── __init__.py         # Application factory
│   ├── helpers/            # Helper modules
│   │   ├── auth.py         # Authentication helpers 
│   │   └── facebook.py     # Facebook API interaction
│   ├── routes/             # Route modules
│   │   ├── auth.py         # Authentication routes
│   │   ├── main.py         # Main pages routes
│   │   └── posts.py        # Post scheduling routes
│   ├── static/             # Static assets
│   ├── templates/          # HTML templates
│   └── uploads/            # Temporary upload directory
├── run.py                  # Application entry point
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
└── requirements.txt        # Python dependencies
```

## Setup Options

### Option 1: Docker Setup (Recommended)

1. Clone this repository
2. Create a `.env` file based on `.env.example`:
   ```
   FACEBOOK_APP_ID=your_facebook_app_id
   FACEBOOK_APP_SECRET=your_facebook_app_secret
   FACEBOOK_REDIRECT_URI=http://localhost:8000/callback
   SECRET_KEY=your-secure-secret-key-for-sessions
   ```
3. Start the application with Docker Compose:
   ```
   docker-compose up -d
   ```
4. Open your browser and go to `http://localhost:8000`

### Option 2: Local Development Setup

1. Clone this repository
2. Create a `.env` file with the required environment variables (see `.env.example`)
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the application:
   ```
   python run.py
   ```
5. Open your browser and go to `http://localhost:8000`

## Facebook App Setup

To use this application, you need to:

1. Create a Facebook Developer account
2. Create a Facebook App
3. Configure the app with the following permissions:
   - pages_manage_posts
   - pages_read_engagement
   - pages_show_list
4. Set up a Valid OAuth Redirect URI in your Facebook App: `http://localhost:8000/callback`

## How to Use

1. Login with your Facebook account
2. Select a Facebook page to post to
3. Enter your message content
4. Choose the date and time to publish
5. Optionally, upload an image
6. Schedule your post!

## Docker Volumes

The Docker setup uses the following persistent volumes:

- `postgres_data`: Stores the PostgreSQL database files
- `./uploads:/app/uploads`: Maps the local uploads directory to the container

## Database Configuration

The application uses PostgreSQL for session storage and can be configured with the `DATABASE_URL` environment variable. When using Docker, this is already configured in the `docker-compose.yml` file.

## Production Deployment

For production deployment, consider:

1. Using a dedicated database server
2. Configuring HTTPS with a proper domain name
3. Setting up proper logging
4. Using a production-ready web server like Gunicorn behind Nginx

## Note

The application uses Flask-Session with filesystem storage by default. In a production environment, you should consider using Redis or a database backend for session storage instead of the filesystem for better performance and reliability. 