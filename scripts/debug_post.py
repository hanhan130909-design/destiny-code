#!/usr/bin/env python3
"""Debug the FB post failure."""
import sys, json, urllib.request, urllib.parse, urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from social_poster import *

cfg = json.loads(open(CONFIG).read())
posted = get_posted(FB_LOG)

blogs = get_all_blogs()
available = [b for b in blogs if b["file"] not in posted]

print(f"Unposted blogs: {len(available)}")

blog = available[0]
print(f"\nSelected: {blog['title'][:80]}")
print(f"URL: {blog['url']}")

# Test caption generation
caption = generate_caption(blog, "fb")
print(f"\nCaption ({len(caption)} chars):")
print(caption[:500])

# Test FB API with more detail
if len(caption) > 600:
    caption = caption[:597] + "..."
    print(f"\nTruncated to {len(caption)} chars")

params = {"message": caption, "access_token": cfg["page_token"], "link": blog["url"]}
data = urllib.parse.urlencode(params).encode("utf-8")

url = f"https://graph.facebook.com/v25.0/{cfg['page_id']}/feed"
print(f"\nPosting to: {url}")
print(f"Params: message={caption[:100]}..., link={blog['url']}")

try:
    r = urllib.request.urlopen(url, data=data, timeout=15)
    result = json.loads(r.read())
    print(f"\nSUCCESS: {result}")
except urllib.error.HTTPError as e:
    body = e.read().decode()
    print(f"\nFAILED: HTTP {e.code}")
    print(f"Response body: {body}")
