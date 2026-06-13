import json, urllib.request, urllib.error
cfg = json.loads(open('config/meta_config.json').read())
token = cfg['page_token']
page_id = cfg['page_id']
try:
    r = urllib.request.urlopen(f'https://graph.facebook.com/v25.0/me?access_token={token}')
    print('Token valid:', json.loads(r.read()))
except urllib.error.HTTPError as e:
    print(f'Token check error {e.code}:', e.read().decode())
