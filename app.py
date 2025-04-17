import os
import requests
import time
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, 
    url_for, flash, session
)
from flask_session import Session
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import psycopg2
from psycopg2.extras import DictCursor

load_dotenv()

app = Flask(__name__)
# Use a fixed secret key instead of generating a new one each time
app.secret_key = os.getenv("SECRET_KEY", "facebook-scheduler-secret-key")
# Set session to last for 60 days (same as the token)
app.config['PERMANENT_SESSION_LIFETIME'] = (
    60 * 24 * 60 * 60  # 60 days in seconds
)

# For simplicity, we'll use filesystem session storage
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = 'flask_session'
os.makedirs('flask_session', exist_ok=True)

# Initialize the session extension
Session(app)

# Configuration
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:8000/callback")
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return ('.' in filename and 
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)

def exchange_token(code):
    """Exchange code for access token"""
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "client_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "client_secret": APP_SECRET,
        "code": code,
    }
    response = requests.get(token_url, params=params)
    response.raise_for_status()
    return response.json()["access_token"]

def get_long_lived_token(short_lived_token):
    """Exchange short-lived token for long-lived token"""
    url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": short_lived_token,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    # Long-lived token typically expires in 60 days (in seconds)
    # Facebook doesn't explicitly return expiration time for long-lived tokens
    # so we calculate it manually (60 days from now)
    expiration_time = int(time.time()) + (60 * 24 * 60 * 60)  # 60 days in seconds
    
    return {
        "access_token": data["access_token"],
        "expires_at": expiration_time
    }

def get_user_pages(access_token):
    """Get pages that user has access to"""
    url = "https://graph.facebook.com/v19.0/me/accounts"
    params = {"access_token": access_token}
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()["data"]

def schedule_text_post(page_id, page_access_token, message, publish_time):
    """Schedule a text-only post"""
    url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
    payload = {
        "message": message,
        "published": "false",
        "scheduled_publish_time": int(publish_time),
        "access_token": page_access_token,
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return {
            "error": True,
            "status_code": e.response.status_code,
            "content": e.response.json()
        }

def schedule_photo_post(page_id, page_access_token, message, image_path, publish_time):
    """Schedule a post with photo"""
    # First, upload the photo
    upload_url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
    
    print(f"Starting photo upload process for: {image_path}")
    print(f"File exists: {os.path.exists(image_path)}")
    print(f"File size: {os.path.getsize(image_path)} bytes")
    
    with open(image_path, 'rb') as image_file:
        upload_payload = {
            "published": "false",  # Don't publish immediately
            "access_token": page_access_token,
        }
        files = {
            "source": image_file
        }
        try:
            print("Sending photo upload request to Facebook API...")
            upload_response = requests.post(upload_url, data=upload_payload, files=files)
            print(f"Upload response status code: {upload_response.status_code}")
            upload_response.raise_for_status()
            upload_result = upload_response.json()
            print(f"Upload response: {upload_result}")
            
            # Check for errors in upload
            if 'error' in upload_result:
                print(f"Error in photo upload: {upload_result['error']}")
                return {
                    "error": True,
                    "status_code": upload_response.status_code,
                    "content": upload_result['error']
                }
            
            # Now schedule the post with the uploaded photo
            photo_id = upload_result.get('id')
            if not photo_id:
                print("No photo ID returned from upload")
                return {
                    "error": True,
                    "status_code": 400,
                    "content": {"message": "Failed to get photo ID from upload"}
                }
            
            print(f"Successfully uploaded photo with ID: {photo_id}")
            
            # Schedule the post
            schedule_url = f"https://graph.facebook.com/v19.0/{page_id}/feed"
            schedule_payload = {
                "message": message,
                "published": "false",
                "scheduled_publish_time": int(publish_time),
                "attached_media[0]": f"{{'media_fbid':'{photo_id}'}}",
                "access_token": page_access_token,
            }
            
            print("Sending scheduling request to Facebook API...")
            schedule_response = requests.post(schedule_url, data=schedule_payload)
            print(f"Schedule response status code: {schedule_response.status_code}")
            schedule_response.raise_for_status()
            schedule_result = schedule_response.json()
            print(f"Schedule response: {schedule_result}")
            
            # Check for errors in scheduling
            if 'error' in schedule_result:
                print(f"Error in scheduling: {schedule_result['error']}")
                return {
                    "error": True,
                    "status_code": schedule_response.status_code,
                    "content": schedule_result['error']
                }
            
            print("Post with photo scheduled successfully!")    
            return schedule_result
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error during photo post scheduling: {str(e)}")
            return {
                "error": True,
                "status_code": e.response.status_code,
                "content": e.response.json()
            }
        except Exception as e:
            print(f"Unexpected error during photo post scheduling: {str(e)}")
            return {
                "error": True,
                "status_code": 500,
                "content": {"message": str(e)}
            }

@app.route('/')
def index():
    """Home page with login button if not authenticated"""
    if 'access_token' not in session:
        login_url = (
            "https://www.facebook.com/v19.0/dialog/oauth"
            f"?client_id={APP_ID}&redirect_uri={REDIRECT_URI}"
            "&scope=pages_manage_posts,pages_read_engagement,pages_show_list"
        )
        return render_template('index.html', login_url=login_url, authenticated=False)
    
    # Calculate token expiration info
    token_expires_at = session.get('token_expires_at', 0)
    current_time = int(time.time())
    
    # Calculate days remaining until expiration
    seconds_remaining = max(0, token_expires_at - current_time)
    days_remaining = seconds_remaining // (24 * 60 * 60)
    
    # Format expiration date for display
    expiration_date = datetime.fromtimestamp(token_expires_at).strftime('%Y-%m-%d')
    
    # If authenticated, show pages
    if 'pages' not in session:
        try:
            pages = get_user_pages(session['access_token'])
            session['pages'] = pages
        except Exception as e:
            flash(f"Error fetching pages: {str(e)}")
            session.clear()
            return redirect(url_for('index'))
    
    return render_template(
        'index.html', 
        authenticated=True, 
        pages=session['pages'],
        token_days_remaining=days_remaining,
        token_expiration_date=expiration_date
    )

@app.route('/callback')
def callback():
    """Handle Facebook OAuth callback"""
    code = request.args.get('code')
    if not code:
        flash('Authorization failed.')
        return redirect(url_for('index'))
    
    try:
        # Get short-lived token
        short_lived_token = exchange_token(code)
        
        # Exchange for long-lived token
        token_data = get_long_lived_token(short_lived_token)
        
        # Make the session permanent
        session.permanent = True
        
        # Save token and expiration to session
        session['access_token'] = token_data['access_token']
        session['token_expires_at'] = token_data['expires_at']
        
        # Get user's pages
        pages = get_user_pages(token_data['access_token'])
        session['pages'] = pages
        
        flash('Successfully logged in!')
    except Exception as e:
        flash(f"Error during authentication: {str(e)}")
    
    return redirect(url_for('index'))

@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    """Schedule post form and handling"""
    if 'access_token' not in session:
        flash('Please log in first.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        page_id = request.form.get('page_id')
        message = request.form.get('message')
        schedule_date = request.form.get('date')
        schedule_time = request.form.get('time')
        
        # Debug logging
        print("Form submission received:")
        print(f"Page ID: '{page_id}'")
        print(f"Message: '{message}'")
        print(f"Date: '{schedule_date}'")
        print(f"Time: '{schedule_time}'")
        print(f"All form data: {request.form}")
        
        # Validate form data
        if not all([page_id, message, schedule_date, schedule_time]):
            missing = []
            if not page_id: missing.append("page")
            if not message: missing.append("message")
            if not schedule_date: missing.append("date")
            if not schedule_time: missing.append("time")
            flash(f'Please fill all required fields. Missing: {", ".join(missing)}')
            return redirect(url_for('schedule'))
        
        # Find page token
        page_token = None
        for page in session['pages']:
            if page['id'] == page_id:
                page_token = page['access_token']
                break
        
        if not page_token:
            flash('Invalid page selected.')
            return redirect(url_for('schedule'))
        
        # Convert date and time to timestamp
        try:
            dt_str = f"{schedule_date} {schedule_time}"
            dt_obj = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
            publish_time = int(dt_obj.timestamp())
            
            # Check if time is in the future
            if publish_time <= int(time.time()):
                flash('Scheduled time must be in the future.')
                return redirect(url_for('schedule'))
        except ValueError:
            flash('Invalid date or time format.')
            return redirect(url_for('schedule'))
        
        # Check if an image was uploaded
        if 'image' in request.files and request.files['image'].filename:
            image = request.files['image']
            print(f"Image upload detected: {image.filename}")
            
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                print(f"Saving image to: {filepath}")
                try:
                    image.save(filepath)
                    print(f"Image saved successfully")
                    
                    # Verify the file exists and has content
                    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
                        print(f"File exists and has size: {os.path.getsize(filepath)} bytes")
                    else:
                        print(f"File verification failed. Exists: {os.path.exists(filepath)}")
                        flash('Error saving image file.')
                        return redirect(url_for('schedule'))
                    
                    # Schedule post with image
                    result = schedule_photo_post(
                        page_id, page_token, message, filepath, publish_time
                    )
                    # Log the result for debugging
                    print(f"Photo post scheduling result: {result}")
                except Exception as e:
                    print(f"Error saving image: {str(e)}")
                    flash(f'Error uploading image: {str(e)}')
                    return redirect(url_for('schedule'))
            else:
                print(f"Invalid file type for: {image.filename}")
                flash('Invalid file type. Only images are allowed.')
                return redirect(url_for('schedule'))
        else:
            # Schedule text-only post
            result = schedule_text_post(
                page_id, page_token, message, publish_time
            )
            # Log the result for debugging
            print(f"Text post scheduling result: {result}")
        
        # Handle result
        if 'error' in result and result['error']:
            error_content = result['content']
            error_message = error_content.get('message', str(error_content))
            flash(f"Error scheduling post: {error_message}")
        else:
            flash('Post scheduled successfully!')
            
        return redirect(url_for('schedule'))
    
    # GET request - show form
    return render_template('schedule.html', pages=session['pages'])

@app.route('/logout')
def logout():
    """Clear session and log out"""
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000, debug=True) 