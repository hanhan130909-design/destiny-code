#!/usr/bin/env python3
"""Auto-post to Instagram via Graph API. Companion to fb_auto_post.py"""
import urllib.request, urllib.parse, json, random, re, time
from pathlib import Path

PROJECT = Path("/home/ubuntu/projects/metaphysics-landing")
CONFIG = PROJECT / "config/meta_config.json"
LOG = PROJECT / "config/ig_post_log.json"

def load_config():
    with open(CONFIG) as f:
        return json.load(f)

def get_blog_posts():
    posts = []
    for f in sorted((PROJECT / "blog").glob("*.html")):
        text = f.read_text()
        h1 = re.search(r'<h1[^>]*>(.+?)</h1>', text)
        posts.append({"file": f.name, "title": h1.group(1) if h1 else f.stem})
    return posts

def get_posted():
    if LOG.exists():
        return set(json.loads(open(LOG).read()).get("posted", []))
    return set()

def save_posted(file_name):
    posted = list(get_posted())
    posted.append(file_name)
    with open(LOG, "w") as f:
        json.dump({"posted": posted}, f, indent=2)

def post_ig(ig_id, token, image_url, caption):
    # Create container
    p = urllib.parse.urlencode({
        "image_url": image_url,
        "caption": caption,
        "access_token": token
    })
    r = urllib.request.urlopen(f"https://graph.facebook.com/v25.0/{ig_id}/media", data=p.encode())
    result = json.loads(r.read())
    cid = result.get("id")
    if not cid:
        return None
    
    # Wait for processing
    for i in range(20):
        time.sleep(2)
        p2 = urllib.parse.urlencode({"fields": "status_code", "access_token": token})
        r2 = urllib.request.urlopen(f"https://graph.facebook.com/v25.0/{cid}?" + p2)
        status = json.loads(r2.read())
        if status.get("status_code") in ("FINISHED", "ERROR"):
            break
    
    # Publish
    p3 = urllib.parse.urlencode({"creation_id": cid, "access_token": token})
    r3 = urllib.request.urlopen(f"https://graph.facebook.com/v25.0/{ig_id}/media_publish", data=p3.encode())
    pub = json.loads(r3.read())
    return pub.get("id")

def main():
    cfg = load_config()
    ig_id = cfg["ig_id"]
    token = cfg["page_token"]
    
    posts = get_blog_posts()
    posted = get_posted()
    available = [p for p in posts if p["file"] not in posted]
    if not available:
        available = posts
        posted = set()
    
    pick = random.choice(available)
    caption = f"{pick['title']}\n\nDiscover your destiny through BaZi — Chinese Astrology decoded.\n\n🔗 metaphysics-landing.vercel.app\n\n#BaZi #ChineseAstrology #DestinyCode #八字"
    
    post_id = post_ig(ig_id, token, "https://metaphysics-landing.vercel.app/og-image.png", caption)
    print(f"Posted: {pick['title'][:50]}")
    print(f"IG Post ID: {post_id}")
    save_posted(pick["file"])

if __name__ == "__main__":
    main()
