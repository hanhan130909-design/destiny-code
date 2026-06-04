#!/usr/bin/env python3
"""
Google/Bing Indexing Pinger — Submits sitemap to search engines.
Call this periodically to request re-indexing.

Usage: python scripts/ping_indexers.py
"""
import urllib.request
import urllib.parse

SITEMAP_URL = "https://metaphysics-landing.vercel.app/sitemap.xml"

PING_URLS = [
    f"https://www.google.com/ping?sitemap={urllib.parse.quote(SITEMAP_URL)}",
    f"https://www.bing.com/ping?sitemap={urllib.parse.quote(SITEMAP_URL)}",
]

for url in PING_URLS:
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("User-Agent", "DestinyCode-Pinger/1.0")
        with urllib.request.urlopen(req, timeout=10) as resp:
            print(f"✅ {url.split('/')[2]}: {resp.status}")
    except Exception as e:
        print(f"❌ {url.split('/')[2]}: {e}")
