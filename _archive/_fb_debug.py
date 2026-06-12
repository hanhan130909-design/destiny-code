#!/usr/bin/env python3
"""Debug Facebook API token and posting."""
import urllib.request, urllib.parse, urllib.error, json

cfg = json.loads(open("config/meta_config.json").read())
page_id = cfg["page_id"]
token = cfg["page_token"]

# Test 1: Check token validity
try:
    r = urllib.request.urlopen(f"https://graph.facebook.com/v25.0/me?access_token={token}")
    result = json.loads(r.read())
    print("Token check:", json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"Token check FAILED (HTTP {e.code}): {body[:500]}")

# Test 2: Check page access
try:
    r = urllib.request.urlopen(f"https://graph.facebook.com/v25.0/{page_id}?fields=id,name,access_token&access_token={token}")
    result = json.loads(r.read())
    print("\nPage info:", json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"\nPage access FAILED (HTTP {e.code}): {body[:500]}")

# Test 3: Try posting a simple message
simple_msg = "Test post - scheduled content test"
params = {"message": simple_msg, "access_token": token}
data = urllib.parse.urlencode(params).encode("utf-8")
try:
    r = urllib.request.urlopen(f"https://graph.facebook.com/v25.0/{page_id}/feed", data=data)
    result = json.loads(r.read())
    print("\nSimple post result:", json.dumps(result, indent=2))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"\nSimple post FAILED (HTTP {e.code}): {body[:1000]}")
