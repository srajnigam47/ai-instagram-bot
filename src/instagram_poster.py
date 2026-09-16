"""
Instagram Poster — Instagram Graph API v21
Uses Authorization: Bearer header for Instagram Login tokens.
"""

import requests
import time

GRAPH_API_BASE = "https://graph.instagram.com/v21.0"

def _headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token.strip()}"}

def verify_token(access_token: str, account_id: str) -> bool:
    token = access_token.strip()
    print(f"  Token length: {len(token)}, prefix: {token[:8]}")
    try:
        response = requests.get(
            f"{GRAPH_API_BASE}/{account_id}",
            headers=_headers(token),
            params={"fields": "id,username,name"},
            timeout=15
        )
        data = response.json()
        if "id" in data:
            print(f"  Token OK — {data.get('username', data.get('name', data['id']))}")
            return True
        print(f"  Token check failed: {data}")
        return False
    except Exception as e:
        print(f"  Token check error: {e}")
        return False

def create_media_container(image_url: str, caption: str, access_token: str, account_id: str, retries: int = 3) -> str | None:
    """Meta's server-side fetch of image_url is known to fail transiently
    even when the URL is perfectly reachable — retry a few times."""
    url = f"{GRAPH_API_BASE}/{account_id}/media"
    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                url,
                headers=_headers(access_token),
                json={
                    "image_url": image_url,
                    "caption": caption,
                    "media_type": "IMAGE",
                },
                timeout=30
            )
            data = response.json()
            if "id" in data:
                print(f"  Media container created: {data['id']}")
                return data["id"]
            print(f"  ❌ Container creation failed (attempt {attempt}/{retries}): {data}")
        except Exception as e:
            print(f"  ❌ Container error (attempt {attempt}/{retries}): {e}")

        if attempt < retries:
            time.sleep(15)

    return None

def wait_for_container(container_id: str, access_token: str, max_wait: int = 60) -> bool:
    url = f"{GRAPH_API_BASE}/{container_id}"
    for _ in range(max_wait // 5):
        time.sleep(5)
        try:
            response = requests.get(
                url,
                headers=_headers(access_token),
                params={"fields": "status_code"},
                timeout=15
            )
            data = response.json()
            status = data.get("status_code", "")
            if status == "FINISHED":
                return True
            elif status == "ERROR":
                print(f"  ❌ Container processing error")
                return False
            print(f"  ⏳ Processing... status: {status}")
        except Exception as e:
            print(f"  Warning: {e}")
    return False

def publish_container(container_id: str, access_token: str, account_id: str) -> str | None:
    url = f"{GRAPH_API_BASE}/{account_id}/media_publish"
    try:
        response = requests.post(
            url,
            headers=_headers(access_token),
            json={"creation_id": container_id},
            timeout=30
        )
        data = response.json()
        if "id" in data:
            return data["id"]
        print(f"  ❌ Publish failed: {data}")
        return None
    except Exception as e:
        print(f"  ❌ Publish error: {e}")
        return None

def post_reel_to_instagram(video_url: str, caption: str, access_token: str, account_id: str) -> str | None:
    """Post a video as an Instagram Reel."""
    url = f"{GRAPH_API_BASE}/{account_id}/media"
    try:
        response = requests.post(
            url,
            headers=_headers(access_token),
            json={
                "video_url": video_url,
                "caption": caption,
                "media_type": "REELS",
                "share_to_feed": "true",
            },
            timeout=30
        )
        data = response.json()
        if "id" in data:
            container_id = data["id"]
            print(f"  Reel container created: {container_id}")
            print("  Waiting for Instagram to process video (up to 2 min)...")
            ready = wait_for_container(container_id, access_token, max_wait=120)
            if not ready:
                print("  Timed out, attempting publish anyway...")
            return publish_container(container_id, access_token, account_id)
        print(f"  ❌ Reel container failed: {data}")
        return None
    except Exception as e:
        print(f"  ❌ Reel error: {e}")
        return None

def post_to_instagram(image_url: str, caption: str, access_token: str, account_id: str) -> str | None:
    print("  Verifying token...")
    if not verify_token(access_token, account_id):
        print("  ❌ Token invalid.")
        return None

    print("  Creating media container...")
    container_id = create_media_container(image_url, caption, access_token, account_id)
    if not container_id:
        return None

    print("  Waiting for Instagram to process image...")
    ready = wait_for_container(container_id, access_token)
    if not ready:
        print("  Status check timed out, attempting publish anyway...")

    print("  Publishing post...")
    return publish_container(container_id, access_token, account_id)
