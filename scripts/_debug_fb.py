#!/usr/bin/env python3
"""Debug Facebook token validity."""
import json, urllib.request, urllib.parse, urllib.error
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
CONFIG = PROJECT / "config/meta_config.json"

cfg = json.loads(open(CONFIG).read())
token = cfg["page_token"]
page_id = cfg["page_id"]

print(f"Token length: {len(token)}")
print(f"Token prefix: {token[:15]}...")
print(f"Token suffix: ...{token[-8:]}")

# Test: get page info
print("\n--- Testing GET /me ---")
try:
    url = f"https://graph.facebook.com/v25.0/me?access_token={token}"
    r = urllib.request.urlopen(url)
    print(f"✅ GET /me: {r.read().decode()}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"❌ HTTP {e.code}: {body}")

# Test: get page info
print("\n--- Testing GET /{page_id} ---")
try:
    url = f"https://graph.facebook.com/v25.0/{page_id}?fields=name&access_token={token}"
    r = urllib.request.urlopen(url)
    print(f"✅ GET page: {r.read().decode()}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"❌ HTTP {e.code}: {body}")
