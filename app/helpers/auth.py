import requests
import time
from flask import current_app


def exchange_token(code):
    """Exchange code for access token"""
    app_id = current_app.config['APP_ID']
    app_secret = current_app.config['APP_SECRET']
    redirect_uri = current_app.config['REDIRECT_URI']
    
    token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "client_secret": app_secret,
        "code": code,
    }
    response = requests.get(token_url, params=params)
    response.raise_for_status()
    return response.json()["access_token"]


def get_long_lived_token(short_lived_token):
    """Exchange short-lived token for long-lived token"""
    app_id = current_app.config['APP_ID']
    app_secret = current_app.config['APP_SECRET']
    
    url = "https://graph.facebook.com/v19.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_token,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    # Long-lived token typically expires in 60 days (in seconds)
    # Facebook doesn't explicitly return expiration time for long-lived tokens
    # so we calculate it manually (60 days from now)
    expiration_time = int(time.time()) + (60 * 24 * 60 * 60)
    
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