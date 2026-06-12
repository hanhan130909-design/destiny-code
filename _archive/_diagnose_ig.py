#!/usr/bin/env python3
import urllib.request, json
with open("/home/ubuntu/projects/metaphysics-landing/config/meta_config.json") as f:
    cfg = json.load(f)
token = cfg["page_token"]
page_id = cfg["page_id"]
ig_id = cfg["ig_id"]

# Test 1: Token debug
print("=== Token Debug ===")
r = urllib.request.urlopen(f"https://graph.facebook.com/v25.0/debug_token?input_token={token}&access_token={token}")
data = json.loads(r.read())
print(json.dumps(data, indent=2))

# Test 2: IG from page
print("\n=== IG Account from Page ===")
r2 = urllib.request.urlopen(f"https://graph.facebook.com/v25.0/{page_id}?fields=instagram_business_account,connected_instagram_account&access_token={token}")
data2 = json.loads(r2.read())
print(json.dumps(data2, indent=2))
