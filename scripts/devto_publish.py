#!/usr/bin/env python3
"""
Dev.to Publisher — Publish Destiny Code blog posts to Dev.to via their REST API.

Usage:
    # Dry-run (list posts, validate, don't publish):
    python scripts/devto_publish.py --dry-run

    # Publish all posts:
    DEVTO_API_KEY=your_key python scripts/devto_publish.py

    # Publish a specific post by slug:
    DEVTO_API_KEY=your_key python scripts/devto_publish.py --slug baZi-vs-western-astrology

Environment variables:
    DEVTO_API_KEY       — Your Dev.to API key (required for publishing)
    DEVTO_ORG_ID        — Optional: organization ID for org-owned posts
    SITE_BASE_URL       — Base URL for canonical URLs (default: https://metaphysics-landing.vercel.app)

Dev.to API docs: https://developers.forem.com/api
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from html.parser import HTMLParser

# --- Constants ---
BLOG_DIR = Path(__file__).resolve().parent.parent / "blog"
DEVTO_API = "https://dev.to/api/articles"
SITE_BASE_URL = os.environ.get("SITE_BASE_URL", "https://metaphysics-landing.vercel.app")

# Tags mapping for Dev.to (max 4 tags per post, lowercase, hyphens)
DEFAULT_TAGS = ["bazi", "chinesemetaphysics", "astrology", "selfdiscovery"]


class BlogPostExtractor(HTMLParser):
    """Extract blog post metadata and body from HTML."""

    def __init__(self):
        super().__init__()
        self.in_article = False
        self.in_style = False
        self.in_script = False
        self.in_nav = False
        self.in_footer = False
        self.in_cta = False
        self.current_tag = None
        self.body_parts = []
        self.tags = []
        self.meta = {}
        self.date = ""

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        class_val = attrs_dict.get("class") or ""
        if tag in ("style", "script"):
            self.in_style = True if tag == "style" else None
            self.in_script = True if tag == "script" else None
        if tag == "nav":
            self.in_nav = True
        if tag == "footer":
            self.in_footer = True
        if tag == "article":
            self.in_article = True
        # Detect CTA boxes
        if "cta-box" in class_val:
            self.in_cta = True
        # Collect tags — only <span class="tag"> (exact match)
        if tag == "span" and class_val.strip() == "tag":
            self.current_tag = "span_tag"
        # Collect meta tags
        if tag == "meta":
            name = attrs_dict.get("name", "")
            prop = attrs_dict.get("property", "")
            content = attrs_dict.get("content", "")
            if name == "description":
                self.meta["description"] = content
            elif prop == "og:title":
                self.meta["og_title"] = content
            elif prop == "og:description":
                self.meta["og_description"] = content
        # Collect date — supports <p class="meta"> and <p class="date">
        if tag == "p" and class_val.strip() in ("meta", "date"):
            self.current_tag = "p_meta"

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False
        if tag == "script":
            self.in_script = False
        if tag == "nav":
            self.in_nav = False
        if tag == "footer":
            self.in_footer = False
        if tag == "span" and self.current_tag == "span_tag":
            self.current_tag = None
        if tag == "p" and self.current_tag == "p_meta":
            self.current_tag = None
        if tag == "div" and self.in_cta:
            self.in_cta = False

    def handle_data(self, data):
        if self.in_style or self.in_script or self.in_nav or self.in_footer or self.in_cta:
            return
        if self.current_tag == "span_tag":
            tag_text = data.strip()
            if tag_text and len(tag_text) < 30:  # sanity check
                self.tags.append(tag_text)
            return
        if self.current_tag == "p_meta":
            # Extract date portion: "June 1, 2026 · 5 min read" or "Published June 2026 · 6 min read"
            text = data.strip()
            # Try full date first
            match = re.match(r"(?:Published\s+)?(\w+ \d{1,2}, \d{4})", text)
            if match:
                self.date = match.group(1)
            else:
                # Fallback: "Published June 2026"
                match = re.match(r"Published\s+(\w+ \d{4})", text)
                if match:
                    self.date = match.group(1)
                else:
                    self.date = text[:50]  # keep raw if can't parse
            return
        if self.in_article:
            text = data.strip()
            if text:
                self.body_parts.append(text)


def html_to_markdown(paragraphs):
    """Convert extracted text paragraphs to Dev.to-compatible Markdown."""
    lines = []
    for p in paragraphs:
        # Skip nav-like snippets
        if p.startswith("←") or p == "☯":
            continue
        # If it looks like a heading (short, all important words capitalized)
        if len(p) < 80 and not p.endswith(".") and p[0].isupper():
            lines.append(f"## {p}")
            lines.append("")
        else:
            lines.append(p)
            lines.append("")
    return "\n".join(lines).strip()


def extract_post(html_path: Path) -> dict:
    """Extract metadata and body from a blog post HTML file."""
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Extract title from <title> tag
    title_match = re.search(r"<title>(.*?)(?:\s*—\s*Destiny Code)?</title>", html)
    title = title_match.group(1).strip() if title_match else html_path.stem

    # Extract description from meta
    desc_match = re.search(r'<meta name="description" content="([^"]*)"', html)
    description = desc_match.group(1) if desc_match else ""

    parser = BlogPostExtractor()
    parser.feed(html)

    slug = html_path.stem
    body_md = html_to_markdown(parser.body_parts)

    # Build Dev.to tags (lowercase, no spaces, max 4)
    tags = parser.tags if parser.tags else DEFAULT_TAGS[:4]
    devto_tags = [t.lower().replace(" ", "").replace("-", "") for t in tags[:4]]

    # Canonical URL
    canonical_url = f"{SITE_BASE_URL}/blog/{slug}"

    return {
        "slug": slug,
        "title": title,
        "description": description or parser.meta.get("description", ""),
        "body_markdown": body_md,
        "tags": devto_tags,
        "canonical_url": canonical_url,
        "date": parser.date,
        "published": True,  # Set to False to save as draft
    }


def publish_to_devto(api_key: str, article: dict, org_id: str | None = None) -> dict:
    """Publish an article to Dev.to via REST API."""
    import urllib.request
    import urllib.error

    payload = {
        "article": {
            "title": article["title"],
            "description": article["description"][:200],  # Dev.to max 200 chars
            "body_markdown": article["body_markdown"],
            "tags": article["tags"],
            "canonical_url": article["canonical_url"],
            "published": article.get("published", True),
        }
    }

    if org_id:
        payload["article"]["organization_id"] = int(org_id)

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        DEVTO_API,
        data=data,
        headers={
            "Content-Type": "application/json",
            "api-key": api_key,
            "User-Agent": "DestinyCode-DevtoPublisher/1.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return {"error": e.code, "message": error_body}


def get_all_posts() -> list:
    """Get all blog post HTML files sorted by filename."""
    posts = sorted(BLOG_DIR.glob("*.html"))
    return posts


def main():
    parser = argparse.ArgumentParser(
        description="Publish Destiny Code blog posts to Dev.to"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate posts and show what would be published without actually publishing",
    )
    parser.add_argument(
        "--slug",
        type=str,
        help="Publish only a specific post (by filename slug, e.g., 'what-is-bazi')",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Publish as draft (not publicly visible)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show full extracted markdown body",
    )
    args = parser.parse_args()

    api_key = os.environ.get("DEVTO_API_KEY")
    org_id = os.environ.get("DEVTO_ORG_ID")

    if not args.dry_run and not api_key:
        print("ERROR: DEVTO_API_KEY environment variable is required for publishing.")
        print("Set it or use --dry-run to validate without publishing.")
        sys.exit(1)

    # Get posts to process
    if args.slug:
        post_path = BLOG_DIR / f"{args.slug}.html"
        if not post_path.exists():
            print(f"ERROR: Post not found: {post_path}")
            sys.exit(1)
        posts = [post_path]
    else:
        posts = get_all_posts()

    if not posts:
        print("No blog posts found.")
        sys.exit(0)

    print(f"{'DRY RUN — ' if args.dry_run else ''}Processing {len(posts)} blog post(s)...\n")

    results = []
    for post_path in posts:
        try:
            article = extract_post(post_path)
            article["published"] = not args.draft
            slug = article["slug"]
            print(f"  📄 {slug}")
            print(f"     Title: {article['title']}")
            print(f"     Desc:  {article['description'][:100]}...")
            print(f"     Tags:  {', '.join(article['tags'])}")
            print(f"     Date:  {article.get('date', 'N/A')}")
            print(f"     Body:  {len(article['body_markdown'])} chars")

            if args.verbose:
                print(f"\n     --- MARKDOWN ---")
                print(article["body_markdown"][:2000])
                print("     --- END ---\n")

            if not args.dry_run:
                print(f"     Publishing to Dev.to...")
                result = publish_to_devto(api_key, article, org_id)
                if "error" in result:
                    print(f"     ❌ Failed: {result.get('message', result['error'])}")
                else:
                    devto_url = result.get("url", "unknown")
                    print(f"     ✅ Published: {devto_url}")
                results.append({"slug": slug, "result": result})
            else:
                results.append({"slug": slug, "status": "validated"})
            print()

        except Exception as e:
            print(f"     ❌ Error: {e}\n")
            results.append({"slug": post_path.stem, "error": str(e)})

    # Summary
    print(f"\n{'='*60}")
    if args.dry_run:
        success = sum(1 for r in results if "status" in r)
        errors = sum(1 for r in results if "error" in r)
        print(f"Dry run complete: {success} valid, {errors} errors")
        print("Run without --dry-run and with DEVTO_API_KEY set to publish.")
    else:
        published = sum(1 for r in results if "result" in r and "error" not in r["result"])
        failed = sum(1 for r in results if "result" in r and "error" in r["result"] or "error" in r)
        print(f"Publishing complete: {published} published, {failed} failed")


if __name__ == "__main__":
    main()
