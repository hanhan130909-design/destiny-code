#!/usr/bin/env python3
"""Quick FB API debug script"""
import urllib.request, urllib.parse, json, sys

cfg = json.load(open('config/meta_config.json'))
page_id = cfg['page_id']
token = cfg['page_token']

# Test 1: Check token validity
try:
    r = urllib.request.urlopen(f'https://graph.facebook.com/v25.0/me?access_token={token}')
    print('Token valid:', json.loads(r.read()))
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'Token check error {e.code}: {body}', file=sys.stderr)

# Test 2: Try posting a simple test message
test_message = "Test post from cron"
params = {"message": test_message, "access_token": token}
data = urllib.parse.urlencode(params).encode("utf-8")
try:
    r = urllib.request.urlopen(f'https://graph.facebook.com/v25.0/{page_id}/feed', data=data)
    result = json.loads(r.read())
    print('Post result:', result)
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f'Post error {e.code}: {body}', file=sys.stderr)
