"""
Instagram Poster — Uses Instagram Graph API (FREE)
Official Meta API — free to use with a Creator/Business account.

Setup guide (in README):
1. Create Facebook Developer account → https://developers.facebook.com/
2. Create an App → Add Instagram Basic Display + Instagram Graph API
3. Connect your Instagram Professional account
4. Get your Access Token + Account ID
"""

import requests
import time

GRAPH_API_BASE = "https://graph.facebook.com/v19.0"

def create_media_container(image_url: str, caption: str, access_token: str, account_id: str) -> str | None:
    """Step 1: Upload image URL to Instagram as a media container."""
    url = f"{GRAPH_API_BASE}/{account_id}/media"
    params = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token,
    }

    try:
        response = requests.post(url, data=params, timeout=30)
        data = response.json()

        if "id" in data:
            print(f"  Media container created: {data['id']}")
            return data["id"]
        else:
            print(f"  ❌ Container creation failed: {data}")
            return None

    except Exception as e:
        print(f"  ❌ Container error: {e}")
        return None

def wait_for_container(container_id: str, access_token: str, max_wait: int = 60) -> bool:
    """Wait for Instagram to process the image (usually 5–15 seconds)."""
    url = f"{GRAPH_API_BASE}/{container_id}"
    params = {"fields": "status_code", "access_token": access_token}

    for _ in range(max_wait // 5):
        time.sleep(5)
        try:
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            status = data.get("status_code", "")

            if status == "FINISHED":
                return True
            elif status == "ERROR":
                print(f"  ❌ Container processing error")
                return False
            else:
                print(f"  ⏳ Processing... status: {status}")
        except Exception as e:
            print(f"  Warning: {e}")

    return False

def publish_container(container_id: str, access_token: str, account_id: str) -> str | None:
    """Step 2: Publish the media container as a real post."""
    url = f"{GRAPH_API_BASE}/{account_id}/media_publish"
    params = {
        "creation_id": container_id,
        "access_token": access_token,
    }

    try:
        response = requests.post(url, data=params, timeout=30)
        data = response.json()

        if "id" in data:
            return data["id"]
        else:
            print(f"  ❌ Publish failed: {data}")
            return None

    except Exception as e:
        print(f"  ❌ Publish error: {e}")
        return None

def post_to_instagram(image_url: str, caption: str, access_token: str, account_id: str) -> str | None:
    """Full posting pipeline: container → wait → publish."""

    print("  Creating media container...")
    container_id = create_media_container(image_url, caption, access_token, account_id)
    if not container_id:
        return None

    print("  Waiting for Instagram to process image...")
    ready = wait_for_container(container_id, access_token)
    if not ready:
        # Try publishing anyway — sometimes status check is unreliable
        print("  Status check timed out, attempting publish anyway...")

    print("  Publishing post...")
    post_id = publish_container(container_id, access_token, account_id)
    return post_id
