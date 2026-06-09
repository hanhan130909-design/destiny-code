#!/usr/bin/env python3
"""Auto-post to Facebook Page from blog content. Runs daily via cron."""
import urllib.request, urllib.parse, json, random, os, re
from pathlib import Path

PROJECT = Path("/home/ubuntu/projects/metaphysics-landing")
CONFIG = PROJECT / "config/meta_config.json"
BLOG = PROJECT / "blog"
LOG = PROJECT / "config/fb_post_log.json"

def load_config():
    with open(CONFIG) as f:
        return json.load(f)

def get_blog_posts():
    posts = []
    for f in sorted(BLOG.glob("*.html")):
        text = f.read_text()
        title = re.search(r'<title>(.+?)</title>', text)
        h1 = re.search(r'<h1[^>]*>(.+?)</h1>', text)
        desc = re.search(r'<meta name="description" content="([^"]+)"', text)
        p = re.search(r'<p>(.{50,200}?)</p>', text)
        
        posts.append({
            "file": f.name,
            "title": h1.group(1) if h1 else (title.group(1) if title else f.stem),
            "desc": desc.group(1) if desc else "",
            "snippet": p.group(1)[:180] if p else "",
        })
    return posts

def get_posted():
    if LOG.exists():
        return set(json.loads(open(LOG).read()).get("posted", []))
    return set()

def save_posted(file_name):
    posted = list(get_posted())
    posted.append(file_name)
    with open(LOG, "w") as f:
        json.dump({"posted": posted, "last": file_name}, f, indent=2)

def post_to_fb(page_id, token, message):
    data = urllib.parse.urlencode({"message": message, "access_token": token})
    r = urllib.request.urlopen(f"https://graph.facebook.com/v25.0/{page_id}/feed", data=data.encode())
    return json.loads(r.read())

def main():
    cfg = load_config()
    pid = cfg["page_id"]
    token = cfg["page_token"]
    
    posts = get_blog_posts()
    posted = get_posted()
    available = [p for p in posts if p["file"] not in posted]
    
    if not available:
        available = posts  # recycle if all posted
        posted = set()
    
    pick = random.choice(available)
    
    caption = f"{pick['snippet']}...\n\n🔮 Read more: https://metaphysics-landing.vercel.app/blog/{pick['file']}\n\n#BaZi #ChineseAstrology #DestinyCode #八字"
    
    result = post_to_fb(pid, token, caption)
    post_id = result.get("id", str(result))
    print(f"Posted: {pick['title'][:50]}")
    print(f"FB Post ID: {post_id}")
    save_posted(pick["file"])

if __name__ == "__main__":
    main()
