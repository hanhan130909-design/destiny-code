#!/usr/bin/env python3
import urllib.request, urllib.parse, json, sys
from pathlib import Path

CONFIG = Path(__file__).resolve().parent.parent / "config/meta_config.json"
cfg = json.loads(open(CONFIG).read())
token = cfg["page_token"]
page_id = cfg["page_id"]

# Debug token
url = f'https://graph.facebook.com/v25.0/debug_token?input_token={token}&access_token={token}'
try:
    r = urllib.request.urlopen(url)
    data = json.loads(r.read())
    print('Token debug:', json.dumps(data, indent=2))
except Exception as e:
    print(f'Token debug error: {e}')

# Try a simple post
url2 = f'https://graph.facebook.com/v25.0/{page_id}/feed'
params = {'message': 'Test post - ignore', 'access_token': token}
try:
    r = urllib.request.urlopen(url2, data=urllib.parse.urlencode(params).encode())
    data = json.loads(r.read())
    print('Post test:', json.dumps(data, indent=2))
except Exception as e:
    print(f'Post error: {e}')
    if hasattr(e, 'read'):
        print('Response:', e.read().decode())
