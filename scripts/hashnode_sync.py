#!/usr/bin/env python3
"""Hashnode Auto-Publisher — sync all 29 blog posts to Hashnode

Setup:
  1. Create account at https://hashnode.com
  2. Get PAT: Settings → Developer → Personal Access Token
  3. Set: export HASHNODE_TOKEN="your_token"
  4. Run: python3 scripts/hashnode_sync.py

Hashnode API: GraphQL, posts via createPublicationStory mutation
"""
import os, re, json, requests, sys, time

TOKEN = os.environ.get("HASHNODE_TOKEN", "")
PUBLICATION_ID = os.environ.get("HASHNODE_PUB_ID", "")  # Your blog's publication ID
BLOG_DIR = "blog"

if not TOKEN:
    print("ERROR: Set HASHNODE_TOKEN environment variable")
    print("Get it from: https://hashnode.com/settings/developer")
    sys.exit(1)

API_URL = "https://gql.hashnode.com"
HEADERS = {"Authorization": TOKEN, "Content-Type": "application/json"}

def graphql(query, variables=None):
    r = requests.post(API_URL, json={"query": query, "variables": variables or {}}, headers=HEADERS, timeout=15)
    if r.status_code != 200:
        print(f"  API error: {r.status_code} {r.text[:200]}")
        return None
    return r.json()

def extract_meta(html_path):
    """Extract title, description, content from blog HTML"""
    with open(html_path) as f:
        html = f.read()
    
    title = re.search(r'<title>(.*?)</title>', html)
    desc = re.search(r'<meta name="description" content="([^"]*)"', html)
    h1 = re.search(r'<h1>(.*?)</h1>', html)
    
    # Extract article body
    article_match = re.search(r'<article>(.*?)</article>', html, re.DOTALL)
    if article_match:
        body = article_match.group(1)
        # Remove nav and footer from body
        body = re.sub(r'<nav>.*?</nav>', '', body, flags=re.DOTALL)
        body = re.sub(r'<footer>.*?</footer>', '', body, flags=re.DOTALL)
    else:
        body = html
    
    return {
        "title": (title.group(1) if title else h1.group(1) if h1 else "Untitled").split(" — ")[0].strip(),
        "subtitle": desc.group(1) if desc else "",
        "contentMarkdown": html_to_md(html),
    }

def html_to_md(html):
    """Simple HTML to markdown converter"""
    # This is simplified — for production use html2text or markdownify
    text = html
    text = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', text)
    text = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1', text)
    text = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1', text)
    text = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', text, flags=re.DOTALL)
    text = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', text)
    text = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', text)
    text = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'[\2](\1)', text)
    text = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '', text)
    text = '\n'.join(line.strip() for line in text.split('\n') if line.strip())
    return text

def publish_post(meta, slug):
    """Publish via Hashnode createPost mutation"""
    mutation = """
    mutation PublishPost($input: PublishPostInput!) {
        publishPost(input: $input) {
            post { id url slug title }
        }
    }
    """
    variables = {
        "input": {
            "title": meta["title"],
            "subtitle": meta["subtitle"][:150],
            "contentMarkdown": meta["contentMarkdown"],
            "slug": slug,
            "tags": [
                {"slug": "astrology", "name": "Astrology"},
                {"slug": "chinese-metaphysics", "name": "Chinese Metaphysics"},
                {"slug": "bazi", "name": "BaZi"},
                {"slug": "self-improvement", "name": "Self Improvement"},
            ],
            "publicationId": PUBLICATION_ID,
            "originalArticleURL": f"https://metaphysics-landing.vercel.app/blog/{slug}",
            "isRepublished": {
                "originalArticleURL": f"https://metaphysics-landing.vercel.app/blog/{slug}"
            },
        }
    }
    result = graphql(mutation, variables)
    if result and "data" in result:
        post = result["data"]["publishPost"]["post"]
        print(f"  ✅ {post['url']}")
        return post
    else:
        print(f"  ❌ {json.dumps(result, indent=2)[:200]}")
        return None


if __name__ == "__main__":
    import glob
    posts = sorted(glob.glob(f"{BLOG_DIR}/*.html"))
    print(f"Found {len(posts)} blog posts\n")
    
    published = 0
    for path in posts:
        slug = os.path.basename(path).replace(".html", "")
        print(f"[{published+1}/{len(posts)}] {slug}")
        meta = extract_meta(path)
        result = publish_post(meta, slug)
        if result:
            published += 1
        time.sleep(2)  # Rate limiting
    
    print(f"\nPublished {published}/{len(posts)} to Hashnode")
