"""
Post pacing state — stored as a small JSON file in the repo via the
GitHub Contents API, since GitHub's own `schedule:` cron is known to
silently skip triggers on low-traffic repos. Instead of relying on 5
exact-time firings all succeeding, the workflow runs a frequent check
(every 30 min) and this module decides whether enough time has passed
to actually post.
"""

import os
import json
import base64
import requests
from datetime import datetime, timezone

GITHUB_API = "https://api.github.com"
STATE_PATH = ".state/last_post.json"


def _headers(token: str) -> dict:
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github+json"}


def get_last_post_time() -> datetime | None:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        return None
    try:
        r = requests.get(
            f"{GITHUB_API}/repos/{repo}/contents/{STATE_PATH}",
            headers=_headers(token), timeout=15,
        )
        if r.status_code != 200:
            return None
        content = base64.b64decode(r.json()["content"]).decode()
        return datetime.fromisoformat(json.loads(content)["last_post_utc"])
    except Exception as e:
        print(f"  State read error: {e}")
        return None


def set_last_post_time() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        return
    try:
        get_r = requests.get(
            f"{GITHUB_API}/repos/{repo}/contents/{STATE_PATH}",
            headers=_headers(token), timeout=15,
        )
        sha = get_r.json().get("sha") if get_r.status_code == 200 else None

        content = json.dumps({"last_post_utc": datetime.now(timezone.utc).isoformat()}).encode()
        payload = {
            "message": "Update last post timestamp",
            "content": base64.b64encode(content).decode(),
            "branch": "main",
        }
        if sha:
            payload["sha"] = sha

        r = requests.put(
            f"{GITHUB_API}/repos/{repo}/contents/{STATE_PATH}",
            headers=_headers(token), json=payload, timeout=15,
        )
        if r.status_code not in (200, 201):
            print(f"  State write failed: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"  State write error: {e}")
