#!/usr/bin/env python3
"""Debug script to test Facebook Graph API posting."""
import json
import urllib.request
import urllib.parse

cfg = json.loads(open("../config/meta_config.json").read())
page_id = cfg["page_id"]
token = cfg["page_token"]

# Test 1: Simple post without link
message = "Test post from Destiny Code"
print(f"=== Test 1: message-only post ===")
params = {"message": message, "access_token": token}
data = urllib.parse.urlencode(params).encode("utf-8")

try:
    r = urllib.request.urlopen(
        f"https://graph.facebook.com/v25.0/{page_id}/feed", data=data
    )
    result = r.read().decode()
    print(f"SUCCESS: {result}")
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}")
    print(f"Response: {e.read().decode()}")

# Test 2: Post with link
print(f"\n=== Test 2: message + link ===")
link = "https://metaphysics-landing.vercel.app/blog"
params2 = {"message": message, "access_token": token, "link": link}
data2 = urllib.parse.urlencode(params2).encode("utf-8")

try:
    r = urllib.request.urlopen(
        f"https://graph.facebook.com/v25.0/{page_id}/feed", data=data2
    )
    result = r.read().decode()
    print(f"SUCCESS: {result}")
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}")
    print(f"Response: {e.read().decode()}")

# Test 3: Check token info
print(f"\n=== Test 3: Debug token ===")
try:
    r = urllib.request.urlopen(
        f"https://graph.facebook.com/v25.0/debug_token?input_token={token}&access_token={token}"
    )
    result = r.read().decode()
    print(f"Token info: {result}")
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}")
    print(f"Response: {e.read().decode()}")
