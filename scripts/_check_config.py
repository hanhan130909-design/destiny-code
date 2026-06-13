import json
cfg = json.loads(open('config/meta_config.json').read())
print('Keys:', list(cfg.keys()))
for k in cfg:
    if k in ('page_token', 'app_secret', 'app_id'):
        print(f'{k}: ...{str(cfg[k])[-8:]} (len={len(str(cfg[k]))})')
    else:
        print(f'{k}: {cfg[k]}')
