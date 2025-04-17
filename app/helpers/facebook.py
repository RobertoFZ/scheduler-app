import os
import requests
import json


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
            upload_response = requests.post(
                upload_url, 
                data=upload_payload, 
                files=files
            )
            print(
                f"Upload response status code: "
                f"{upload_response.status_code}"
            )
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
                "attached_media[0]": json.dumps({"media_fbid": photo_id}),
                "access_token": page_access_token,
            }
            
            print("Sending scheduling request to Facebook API...")
            schedule_response = requests.post(
                schedule_url, 
                data=schedule_payload
            )
            print(
                f"Schedule response status code: "
                f"{schedule_response.status_code}"
            )
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
            error_msg = (
                f"Unexpected error during photo post scheduling: {str(e)}"
            )
            print(error_msg)
            return {
                "error": True,
                "status_code": 500,
                "content": {"message": str(e)}
            } 