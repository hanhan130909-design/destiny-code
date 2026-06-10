#!/usr/bin/env python3
"""
Destiny Code Social Auto-Poster v2
- AI-generated captions via DeepSeek API (reads blog, produces post text)
- Posts to FB Page + IG simultaneously
- Tracks posted blogs, picks next unposted by priority
- Designed for cron: every 4 hours = 6 posts/day

Usage: python3 scripts/social_poster.py [--dry-run] [--platform fb|ig|both]
"""
import urllib.request, urllib.parse, json, random, re, time, os, sys, textwrap
from pathlib import Path
from datetime import datetime

PROJECT = Path(__file__).resolve().parent.parent
CONFIG = PROJECT / "config/meta_config.json"
BLOG_DIR = PROJECT / "blog"
FB_LOG = PROJECT / "config/fb_post_log.json"
IG_LOG = PROJECT / "config/ig_post_log.json"

# DeepSeek API
DS_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DS_BASE = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
DS_MODEL = os.environ.get("DEEPSEEK_MODEL", "deepseek-chat")

# ——— Blog Parser ———

def parse_blog(path: Path) -> dict:
    """Extract metadata and body from a blog HTML file."""
    text = path.read_text()
    h1 = re.search(r'<h1[^>]*>(.+?)</h1>', text)
    desc = re.search(r'<meta name="description" content="([^"]+)"', text)
    # Extract first 3 paragraphs as content sample
    paragraphs = re.findall(r'<p>(.{80,500}?)</p>', text, re.DOTALL)
    content_sample = " ".join(p.strip() for p in paragraphs[:3])
    return {
        "file": path.name,
        "slug": path.stem,
        "title": h1.group(1) if h1 else path.stem.replace("-", " ").title(),
        "desc": desc.group(1) if desc else "",
        "content": content_sample[:1200],
        "url": f"https://metaphysics-landing.vercel.app/blog/{path.name}",
    }

def get_all_blogs() -> list:
    blogs = []
    for f in sorted(BLOG_DIR.glob("*.html")):
        try:
            blogs.append(parse_blog(f))
        except Exception:
            pass
    return blogs

# ——— AI Caption Generator ———

def generate_caption(blog: dict, platform: str) -> str:
    """Use DeepSeek to generate an engaging social caption from blog content."""
    if not DS_KEY:
        return fallback_caption(blog, platform)

    style = {
        "fb": "Facebook post: engaging, conversational, 2-3 short paragraphs. Include a hook question. No hashtags. End with link.",
        "ig": "Instagram caption: punchy, emoji-rich, short lines, 150 words max. Include 5-8 relevant hashtags at end. Good hook first line.",
    }.get(platform, "social media post")

    prompt = f"""Write a {style}

Blog: {blog['title']}
Content: {blog['content'][:600]}

Generate the post text ONLY. No markdown, no quotes around it."""

    try:
        req = urllib.request.Request(
            f"{DS_BASE}/chat/completions",
            data=json.dumps({
                "model": DS_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a social media copywriter for a BaZi Chinese Astrology brand. Write engaging, spiritual but grounded content. Never use fear or negative predictions."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.8,
                "max_tokens": 400,
            }).encode(),
            headers={"Authorization": f"Bearer {DS_KEY}", "Content-Type": "application/json"},
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=20).read())
        caption = resp["choices"][0]["message"]["content"].strip()
        if caption:
            return caption
    except Exception as e:
        print(f"  AI caption failed: {e}", file=sys.stderr)
    
    return fallback_caption(blog, platform)

def fallback_caption(blog: dict, platform: str) -> str:
    """Fallback caption without AI."""
    if platform == "fb":
        return f"{blog['desc']}\n\nDiscover what your birth chart reveals about you →\n{blog['url']}"
    else:
        return f"🔮 {blog['title']}\n\n{blog['desc'][:120]}...\n\nLink in bio ↑\n.\n#BaZi #ChineseAstrology #DestinyCode #八字 #EnergyBlueprint"

# ——— Posting Functions ———

def post_fb(page_id: str, token: str, message: str, link: str = None) -> str:
    """Post to Facebook Page feed. Returns post ID."""
    # Truncate message if needed (FB recommends under 500 chars for link posts)
    if len(message) > 600:
        message = message[:597] + "..."
    params = {"message": message, "access_token": token}
    if link:
        params["link"] = link
    data = urllib.parse.urlencode(params).encode("utf-8")
    r = urllib.request.urlopen(
        f"https://graph.facebook.com/v25.0/{page_id}/feed",
        data=data
    )
    result = json.loads(r.read())
    return result.get("id", str(result))

def post_ig(ig_id: str, token: str, caption: str, image_url: str = None) -> str:
    """Post to Instagram. Returns post ID or None."""
    if not image_url:
        image_url = "https://metaphysics-landing.vercel.app/og-image.png"
    
    # Step 1: Create media container
    params = {"caption": caption, "access_token": token, "image_url": image_url}
    r = urllib.request.urlopen(
        f"https://graph.facebook.com/v25.0/{ig_id}/media",
        data=urllib.parse.urlencode(params).encode("utf-8")
    )
    result = json.loads(r.read())
    cid = result.get("id")
    if not cid:
        return None

    # Step 2: Wait for processing
    for _ in range(15):
        time.sleep(2)
        r2 = urllib.request.urlopen(
            f"https://graph.facebook.com/v25.0/{cid}?fields=status_code&access_token={token}"
        )
        status = json.loads(r2.read())
        if status.get("status_code") in ("FINISHED", "ERROR"):
            break

    # Step 3: Publish
    r3 = urllib.request.urlopen(
        f"https://graph.facebook.com/v25.0/{ig_id}/media_publish",
        data=urllib.parse.urlencode({"creation_id": cid, "access_token": token}).encode()
    )
    pub = json.loads(r3.read())
    return pub.get("id")

# ——— Log Management ———

def get_posted(log_path: Path) -> set:
    if log_path.exists():
        try:
            return set(json.loads(open(log_path).read()).get("posted", []))
        except Exception:
            return set()
    return set()

def save_posted(log_path: Path, file_name: str):
    posted = list(get_posted(log_path))
    posted.append(file_name)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        json.dump({"posted": posted, "last": file_name, "last_at": datetime.now().isoformat()}, f, indent=2)

# ——— Main ———

def main():
    dry_run = "--dry-run" in sys.argv
    platforms = sys.argv[sys.argv.index("--platform") + 1] if "--platform" in sys.argv else "both"

    cfg = json.loads(open(CONFIG).read())
    page_id = cfg["page_id"]
    ig_id = cfg["ig_id"]
    token = cfg["page_token"]

    blogs = get_all_blogs()
    print(f"📚 {len(blogs)} blogs found")

    # FB
    if platforms in ("fb", "both"):
        posted_fb = get_posted(FB_LOG)
        available = [b for b in blogs if b["file"] not in posted_fb]
        if available:
            blog = random.choice(available)
            print(f"\n📘 FB → {blog['title'][:60]}")
            caption = generate_caption(blog, "fb")
            if not dry_run:
                pid = post_fb(page_id, token, caption, blog["url"])
                save_posted(FB_LOG, blog["file"])
                print(f"  ✅ Posted: {pid}")
            else:
                print(f"  [DRY RUN] Caption ({len(caption)} chars):\n  {caption[:200]}...")
        else:
            print("📘 FB: all posted, nothing new")

    # IG
    if platforms in ("ig", "both"):
        posted_ig = get_posted(IG_LOG)
        available = [b for b in blogs if b["file"] not in posted_ig]
        if available:
            blog = random.choice(available)
            print(f"\n📸 IG → {blog['title'][:60]}")
            caption = generate_caption(blog, "ig")
            if not dry_run:
                pid = post_ig(ig_id, token, caption)
                if pid:
                    save_posted(IG_LOG, blog["file"])
                    print(f"  ✅ Posted: {pid}")
                else:
                    print(f"  ❌ Failed to publish")
            else:
                print(f"  [DRY RUN] Caption ({len(caption)} chars):\n  {caption[:200]}...")
        else:
            print("📸 IG: all posted, nothing new")

if __name__ == "__main__":
    main()
