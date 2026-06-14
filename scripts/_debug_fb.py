#!/usr/bin/env python3
import json, urllib.request, urllib.parse, sys

cfg = json.load(open("/home/ubuntu/projects/metaphysics-landing/config/meta_config.json"))
page_id = cfg["page_id"]
token = cfg["page_token"]

# Test 1: Validate token with token debug endpoint
print("=== Token Debug ===")
try:
    url = f"https://graph.facebook.com/debug_token?input_token={token}&access_token={token}"
    r = urllib.request.urlopen(url, timeout=15)
    data = json.loads(r.read())
    print(json.dumps(data, indent=2))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body}")

# Test 2: Check page access
print("\n=== Page Access ===")
try:
    url = f"https://graph.facebook.com/v25.0/{page_id}?fields=name,access_token&access_token={token}"
    r = urllib.request.urlopen(url, timeout=15)
    data = json.loads(r.read())
    print(json.dumps(data, indent=2))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body}")

# Test 3: Try to post a minimal test
print("\n=== Test Post ===")
try:
    from datetime import datetime
    test_msg = f"Test post from cron debug at {datetime.now().isoformat()[:19]}"
    params = {"message": test_msg, "access_token": token}
    data_enc = urllib.parse.urlencode(params).encode("utf-8")
    r = urllib.request.urlopen(f"https://graph.facebook.com/v25.0/{page_id}/feed", data=data_enc)
    result = json.loads(r.read())
    print(json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"HTTP {e.code}: {body}")
