#!/usr/bin/env python3
"""Debug IG API call"""
import json, sys, urllib.request, urllib.parse, urllib.error

cfg = json.loads(open("config/meta_config.json").read())
token = cfg["page_token"]
ig_id = cfg["ig_id"]
image_url = "https://metaphysics-landing.vercel.app/og-image.png"
caption = "Test caption"

params = {"caption": caption, "access_token": token, "image_url": image_url}
url = f"https://graph.facebook.com/v25.0/{ig_id}/media"

try:
    req = urllib.request.Request(url, data=urllib.parse.urlencode(params).encode("utf-8"))
    r = urllib.request.urlopen(req, timeout=30)
    print("STATUS:", r.status)
    print("RESPONSE:", r.read().decode())
except urllib.error.HTTPError as e:
    print("HTTP ERROR:", e.code)
    print("RESPONSE:", e.read().decode())
except Exception as ex:
    print("EXCEPTION:", type(ex).__name__, str(ex))
