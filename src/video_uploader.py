"""
Video Uploader — uses GitHub Releases as temporary public video hosting.
Uploads video → gets public URL → posts to Instagram → deletes release.
No extra accounts needed.
"""

import requests
import time
import os

GITHUB_API = "https://api.github.com"

def upload_video(video_bytes: bytes) -> tuple[str | None, str | None]:
    """
    Upload video to a GitHub Release.
    Returns (public_url, release_id) or (None, None) on failure.
    """
    token = os.environ.get("GITHUB_TOKEN")
    repo  = os.environ.get("GITHUB_REPOSITORY")

    if not token or not repo:
        print("  Missing GITHUB_TOKEN or GITHUB_REPOSITORY env vars")
        return None, None

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }
    tag = f"tmp-video-{int(time.time())}"

    # Create release
    try:
        r = requests.post(
            f"{GITHUB_API}/repos/{repo}/releases",
            headers=headers,
            json={
                "tag_name": tag,
                "name": tag,
                "prerelease": True,
                "draft": False,
            },
            timeout=30
        )
        release = r.json()
        release_id = str(release["id"])
        upload_url = release["upload_url"].split("{")[0]
        print(f"  GitHub release created: {tag}")
    except Exception as e:
        print(f"  Release creation failed: {e}")
        return None, None

    # Upload video asset
    try:
        filename = f"{tag}.mp4"
        r = requests.post(
            upload_url,
            headers={**headers, "Content-Type": "video/mp4"},
            params={"name": filename},
            data=video_bytes,
            timeout=120
        )
        asset = r.json()
        public_url = asset.get("browser_download_url")
        print(f"  Video uploaded: {public_url}")
        return public_url, release_id
    except Exception as e:
        print(f"  Video upload failed: {e}")
        return None, release_id

def delete_release(release_id: str):
    """Delete the temporary release after Instagram has processed the video."""
    token = os.environ.get("GITHUB_TOKEN")
    repo  = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo or not release_id:
        return
    try:
        requests.delete(
            f"{GITHUB_API}/repos/{repo}/releases/{release_id}",
            headers={"Authorization": f"token {token}"},
            timeout=15
        )
        print(f"  Temporary release deleted")
    except Exception as e:
        print(f"  Release cleanup failed (non-critical): {e}")
