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

## Deploying to Render.com

This application is configured for easy deployment on Render.com using the provided `render.yaml` blueprint file.

### Deployment Services

The application consists of two main services:

1. **Web Service**: The main Flask application that handles user requests, authentication, and UI
2. **Scheduler (Cron Job)**: A scheduled task that runs every hour to process pending posts

Both services use the free tier on Render.com.

### Deployment Steps

1. Fork or push this repository to GitHub.

2. Create a new Render.com account or sign in to your existing account.

3. On your Render dashboard, click "New" and select "Blueprint".

4. Connect your GitHub account and select this repository.

5. Configure the required environment variables:
   - `DATABASE_URL` - Connection string for your PostgreSQL database
   - `FACEBOOK_APP_ID` - Your Facebook App ID
   - `FACEBOOK_APP_SECRET` - Your Facebook App Secret
   - `FACEBOOK_REDIRECT_URI` - The callback URL (e.g., https://your-app.onrender.com/callback)

6. Click "Apply" to deploy the application.

### Important Considerations

#### Scheduler Frequency

The scheduler is configured to run as a cron job every hour (`0 * * * *`). This means:
- It will check for posts to schedule once per hour
- It will only run for a short time and then exit (not a continuous process)
- This approach is compatible with Render's free tier

If you need a different frequency, you can modify the `schedule` parameter in the `render.yaml` file. For example:
- Every 30 minutes: `*/30 * * * *`
- Every 15 minutes: `*/15 * * * *`
- Twice per hour: `0,30 * * * *`

#### File Storage

Render.com uses ephemeral file storage, which means any files uploaded to the container (like post images) will be lost when the service restarts or when a new deployment occurs. 

For production use, consider these options:

1. **Render Disk** (paid feature): Attach a persistent disk to your service
   - Update the Dockerfile to use this mounted directory for uploads

2. **Cloud Storage Solution**: Modify the application to use a cloud storage provider
   - AWS S3
   - Google Cloud Storage
   - Azure Blob Storage

#### External Database

For the free tier deployment, you'll need to use an external PostgreSQL database as Render's managed database service doesn't have a free tier. Some options include:
- [Supabase](https://supabase.com/) (free tier available)
- [Neon](https://neon.tech/) (free tier available)
- [ElephantSQL](https://www.elephantsql.com/) (free tier available)

#### Environment Variables

All necessary environment variables are specified in the `render.yaml` file. Some variables are marked with `sync: false`, which means you'll need to set them manually in the Render dashboard after the initial deployment. 