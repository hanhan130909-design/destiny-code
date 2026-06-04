"""
GitHub-based persistent storage for Vercel serverless functions.
Replaces /tmp/shelve with GitHub repo JSON files.

Files in repo:
  data/submissions.json  → list of form submissions
  data/followups.json    → dict of followup send statuses
"""
import os
import json
import base64
import requests

GH_TOKEN = os.environ.get("GH_TOKEN", "")
REPO = "hanhan130909-design/destiny-code"
API_BASE = f"https://api.github.com/repos/{REPO}/contents/data"

HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github.v3+json",
}


def _get_file(filename):
    """Read a JSON file from GitHub repo. Returns parsed JSON or default."""
    url = f"{API_BASE}/{filename}"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        return json.loads(content), data.get("sha", "")
    elif resp.status_code == 404:
        return None, ""
    else:
        print(f"[github_db] GET {filename} → {resp.status_code}: {resp.text[:200]}")
        return None, ""


def _put_file(filename, data, sha=""):
    """Write a JSON file to GitHub repo. Returns True on success."""
    url = f"{API_BASE}/{filename}"
    content_b64 = base64.b64encode(
        json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    ).decode("ascii")

    body = {
        "message": f"Update {filename}",
        "content": content_b64,
    }
    if sha:
        body["sha"] = sha

    resp = requests.put(url, headers=HEADERS, json=body, timeout=15)
    if resp.status_code in (200, 201):
        return True
    else:
        print(f"[github_db] PUT {filename} → {resp.status_code}: {resp.text[:200]}")
        return False


def read_submissions():
    """Read all submissions."""
    data, _ = _get_file("submissions.json")
    return data if data else []


def append_submission(entry):
    """Append a submission entry."""
    submissions, sha = _get_file("submissions.json")
    if submissions is None:
        submissions = []
    submissions.append(entry)
    if len(submissions) > 200:
        submissions = submissions[-200:]
    return _put_file("submissions.json", submissions, sha)


def read_followups():
    """Read followup sent status dict."""
    data, _ = _get_file("followups.json")
    return data if data else {}


def save_followups(data):
    """Save followup sent status dict."""
    _, sha = _get_file("followups.json")
    return _put_file("followups.json", data, sha)
