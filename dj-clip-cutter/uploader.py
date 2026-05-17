"""
Social platform upload module.
Handles uploading clips to TikTok, Instagram, and YouTube Shorts.
Requires API credentials configured in config.json.
"""

import os
import json
import subprocess

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')


def load_config():
    """Load API credentials from config.json."""
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(config):
    """Save API credentials to config.json."""
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)


def get_platform_status():
    """Check which platforms are configured."""
    config = load_config()
    return {
        'youtube': {
            'configured': bool(config.get('youtube', {}).get('client_id')),
            'authenticated': bool(config.get('youtube', {}).get('access_token')),
        },
        'tiktok': {
            'configured': bool(config.get('tiktok', {}).get('access_token')),
            'authenticated': bool(config.get('tiktok', {}).get('access_token')),
        },
        'instagram': {
            'configured': bool(config.get('instagram', {}).get('access_token')),
            'authenticated': bool(config.get('instagram', {}).get('access_token')),
        },
        'facebook': {
            'configured': bool(config.get('facebook', {}).get('access_token')),
            'authenticated': bool(config.get('facebook', {}).get('access_token')),
        },
    }


# ---- YouTube Shorts ----

def upload_to_youtube(video_path, title, description="", tags=None, privacy="private"):
    """
    Upload a video to YouTube as a Short.
    Requires google-api-python-client and google-auth-oauthlib.

    Steps to set up:
    1. Go to console.cloud.google.com
    2. Create a project, enable YouTube Data API v3
    3. Create OAuth 2.0 credentials (desktop app)
    4. Download client_secret.json and save as youtube_client_secret.json in the dj-clip-cutter folder
    5. Run: python3 uploader.py youtube-auth
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        return {
            'success': False,
            'error': 'YouTube upload requires: pip install google-api-python-client google-auth-oauthlib'
        }

    config = load_config()
    youtube_config = config.get('youtube', {})

    if not youtube_config.get('access_token'):
        return {'success': False, 'error': 'YouTube not authenticated. Run: python3 uploader.py youtube-auth'}

    try:
        creds = Credentials(
            token=youtube_config['access_token'],
            refresh_token=youtube_config.get('refresh_token'),
            token_uri='https://oauth2.googleapis.com/token',
            client_id=youtube_config.get('client_id'),
            client_secret=youtube_config.get('client_secret'),
        )

        youtube = build('youtube', 'v3', credentials=creds)

        body = {
            'snippet': {
                'title': title[:100],
                'description': description,
                'tags': tags or ['djset', 'music', 'live'],
                'categoryId': '10',  # Music
            },
            'status': {
                'privacyStatus': privacy,
                'selfDeclaredMadeForKids': False,
            }
        }

        media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
        request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)

        response = None
        while response is None:
            _, response = request.next_chunk()

        return {
            'success': True,
            'video_id': response['id'],
            'url': f"https://youtube.com/shorts/{response['id']}"
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def youtube_auth():
    """Interactive OAuth flow for YouTube."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Install: pip install google-api-python-client google-auth-oauthlib")
        return

    secret_path = os.path.join(os.path.dirname(__file__), 'youtube_client_secret.json')
    if not os.path.exists(secret_path):
        print(f"Download OAuth client secret from Google Cloud Console")
        print(f"Save it as: {secret_path}")
        return

    flow = InstalledAppFlow.from_client_secrets_file(
        secret_path,
        scopes=['https://www.googleapis.com/auth/youtube.upload']
    )
    creds = flow.run_local_server(port=8090)

    config = load_config()
    config['youtube'] = {
        'access_token': creds.token,
        'refresh_token': creds.refresh_token,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
    }
    save_config(config)
    print("YouTube authenticated successfully!")


# ---- TikTok ----

def upload_to_tiktok(video_path, title, tags=None):
    """
    Upload a video to TikTok.

    TikTok's Content Posting API requires:
    1. A TikTok Developer account (developers.tiktok.com)
    2. Create an app and get client_key and client_secret
    3. OAuth flow to get access_token
    4. Save access_token in config.json under tiktok.access_token
    """
    try:
        import requests
    except ImportError:
        return {'success': False, 'error': 'pip install requests'}

    config = load_config()
    tiktok_config = config.get('tiktok', {})
    access_token = tiktok_config.get('access_token')

    if not access_token:
        return {
            'success': False,
            'error': 'TikTok not configured. Add your access_token to config.json under tiktok.access_token'
        }

    try:
        # Step 1: Initialize upload
        file_size = os.path.getsize(video_path)
        init_url = 'https://open.tiktokapis.com/v2/post/publish/video/init/'
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
        init_body = {
            'post_info': {
                'title': title[:150],
                'privacy_level': 'SELF_ONLY',
                'disable_comment': False,
                'disable_duet': False,
                'disable_stitch': False,
            },
            'source_info': {
                'source': 'FILE_UPLOAD',
                'video_size': file_size,
                'chunk_size': file_size,
                'total_chunk_count': 1,
            }
        }

        resp = requests.post(init_url, headers=headers, json=init_body)
        resp.raise_for_status()
        data = resp.json()

        upload_url = data['data']['upload_url']

        # Step 2: Upload the file
        with open(video_path, 'rb') as f:
            upload_headers = {
                'Content-Type': 'video/mp4',
                'Content-Range': f'bytes 0-{file_size - 1}/{file_size}',
            }
            upload_resp = requests.put(upload_url, headers=upload_headers, data=f)
            upload_resp.raise_for_status()

        return {
            'success': True,
            'publish_id': data['data'].get('publish_id', 'unknown'),
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ---- Instagram Reels ----

def upload_to_instagram(video_path, caption, tags=None):
    """
    Upload a video as an Instagram Reel.

    Requires:
    1. A Meta Developer account (developers.facebook.com)
    2. An Instagram Business/Creator account connected to a Facebook Page
    3. Access token with instagram_content_publish permission
    4. Save access_token and ig_user_id in config.json under instagram
    """
    try:
        import requests
    except ImportError:
        return {'success': False, 'error': 'pip install requests'}

    config = load_config()
    ig_config = config.get('instagram', {})
    access_token = ig_config.get('access_token')
    ig_user_id = ig_config.get('ig_user_id')

    if not access_token or not ig_user_id:
        return {
            'success': False,
            'error': 'Instagram not configured. Add access_token and ig_user_id to config.json under instagram'
        }

    try:
        # Instagram Reels API requires the video to be publicly accessible via URL
        # For local files, you'd need to host them temporarily
        # This implementation assumes you have a publicly accessible URL
        # For local development, consider using ngrok or similar

        video_url = ig_config.get('temp_video_url')
        if not video_url:
            return {
                'success': False,
                'error': 'Instagram requires a public video URL. Set up a temp hosting solution or use the download+manual approach.'
            }

        # Step 1: Create media container
        container_url = f'https://graph.facebook.com/v18.0/{ig_user_id}/media'
        container_params = {
            'media_type': 'REELS',
            'video_url': video_url,
            'caption': caption[:2200],
            'access_token': access_token,
        }

        resp = requests.post(container_url, params=container_params)
        resp.raise_for_status()
        container_id = resp.json()['id']

        # Step 2: Publish
        publish_url = f'https://graph.facebook.com/v18.0/{ig_user_id}/media_publish'
        publish_params = {
            'creation_id': container_id,
            'access_token': access_token,
        }

        pub_resp = requests.post(publish_url, params=publish_params)
        pub_resp.raise_for_status()

        return {
            'success': True,
            'media_id': pub_resp.json().get('id'),
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ---- Facebook Reels ----

def upload_to_facebook(video_path, title, description="", tags=None):
    """
    Upload a video as a Facebook Reel.

    Requires:
    1. A Meta Developer account (developers.facebook.com)
    2. A Facebook Page with the page_id
    3. Access token with pages_manage_posts and pages_read_engagement permissions
    4. Save access_token and page_id in config.json under facebook

    The Facebook Reels API uses a resumable upload flow:
      - Initialize an upload session
      - Upload the video file in chunks (or single part for files < 1GB)
      - Publish the reel
    """
    try:
        import requests
    except ImportError:
        return {'success': False, 'error': 'pip install requests'}

    config = load_config()
    fb_config = config.get('facebook', {})
    access_token = fb_config.get('access_token')
    page_id = fb_config.get('page_id')

    if not access_token or not page_id:
        return {
            'success': False,
            'error': 'Facebook not configured. Add access_token and page_id to config.json under facebook'
        }

    try:
        file_size = os.path.getsize(video_path)

        # Step 1: Initialize upload session
        init_url = f'https://graph.facebook.com/v18.0/{page_id}/video_reels'
        init_params = {
            'upload_phase': 'start',
            'access_token': access_token,
        }
        resp = requests.post(init_url, params=init_params)
        resp.raise_for_status()
        video_id = resp.json()['video_id']

        # Step 2: Upload video binary
        upload_url = f'https://rupload.facebook.com/video-upload/v18.0/{video_id}'
        upload_headers = {
            'Authorization': f'OAuth {access_token}',
            'offset': '0',
            'file_size': str(file_size),
            'Content-Type': 'application/octet-stream',
        }

        with open(video_path, 'rb') as f:
            upload_resp = requests.post(upload_url, headers=upload_headers, data=f)
            upload_resp.raise_for_status()

        # Step 3: Publish the reel
        publish_url = f'https://graph.facebook.com/v18.0/{page_id}/video_reels'
        publish_params = {
            'upload_phase': 'finish',
            'video_id': video_id,
            'title': title[:255],
            'description': description[:1000] if description else title,
            'access_token': access_token,
        }
        pub_resp = requests.post(publish_url, params=publish_params)
        pub_resp.raise_for_status()

        return {
            'success': True,
            'video_id': video_id,
            'post_id': pub_resp.json().get('id', video_id),
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ---- CLI for auth flows ----

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 uploader.py youtube-auth    # Authenticate with YouTube")
        print("  python3 uploader.py status           # Check platform status")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == 'youtube-auth':
        youtube_auth()
    elif cmd == 'status':
        status = get_platform_status()
        for platform, info in status.items():
            configured = 'Yes' if info['configured'] else 'No'
            authenticated = 'Yes' if info['authenticated'] else 'No'
            print(f"  {platform}: configured={configured}, authenticated={authenticated}")
    else:
        print(f"Unknown command: {cmd}")
