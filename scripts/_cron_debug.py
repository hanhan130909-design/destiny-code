#!/usr/bin/env python3
"""Quick token + URL debug for cron jobs."""
import json, urllib.request, urllib.error, re
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
cfg = json.loads(open(PROJECT / "config/meta_config.json").read())
token = cfg["page_token"]
page_id = cfg["page_id"]

# Token check
print("=== Token (me) ===")
try:
    r = urllib.request.urlopen(f"https://graph.facebook.com/v25.0/me?fields=id,name&access_token={token}", timeout=10)
    print(f"OK: {json.loads(r.read())}")
except urllib.error.HTTPError as e:
    print(f"FAIL ({e.code}): {e.read().decode()[:500]}")

# Page check
print("\n=== Page ===")
try:
    r = urllib.request.urlopen(f"https://graph.facebook.com/v25.0/{page_id}?fields=name,access_token&access_token={token}", timeout=10)
    print(f"OK: {json.loads(r.read())}")
except urllib.error.HTTPError as e:
    print(f"FAIL ({e.code}): {e.read().decode()[:500]}")

# Test post with minimal content
print("\n=== Test Post (minimal) ===")
test_msg = "Test post from auto-poster — will be deleted immediately"
params = {"message": test_msg, "access_token": token}
try:
    data = urllib.parse.urlencode(params).encode("utf-8")
    r = urllib.request.urlopen(f"https://graph.facebook.com/v25.0/{page_id}/feed", data=data, timeout=15)
    result = json.loads(r.read())
    pid = result.get("id", "")
    print(f"POST OK: {pid}")
    # Delete it
    if pid:
        del_data = urllib.parse.urlencode({"access_token": token}).encode()
        urllib.request.urlopen(f"https://graph.facebook.com/v25.0/{pid}", data=del_data, timeout=10)
        print(f"  -> Deleted test post {pid}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"POST FAIL ({e.code}): {body[:800]}")
