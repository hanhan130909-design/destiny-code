#!/usr/bin/env python3
"""
Destiny Code — Social Media Content Scheduler
=============================================
Reads all content files in the project and outputs a publish-ready JSON schedule.

Content sources:
  - reddit-week1-ready/      (3 Reddit discussion posts)
  - tiktok-week1-drafts/     (3 TikTok video scripts)
  - content/twitter-week1.md (5 Twitter/X thread drafts)
  - week1-social-content.md  (Instagram + Pinterest content master)

Usage:
  python3 scripts/social_scheduler.py                          # All platforms → stdout
  python3 scripts/social_scheduler.py --platform twitter       # Twitter only
  python3 scripts/social_scheduler.py -p reddit -p tiktok       # Multiple platforms
  python3 scripts/social_scheduler.py --dry-run                 # Validate only
  python3 scripts/social_scheduler.py -o schedule.json          # Write to file
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional


# ══════════════════════════════════════════════════════════════
# Data Model
# ══════════════════════════════════════════════════════════════

@dataclass
class SocialPost:
    """A single post/piece of content ready for scheduling."""
    platform: str               # reddit | tiktok | twitter | instagram | pinterest
    title: str                  # Post title / video title / tweet hook
    body: str                   # Main content body (caption, tweet text, post body)
    scheduled_time: str         # Human-readable time e.g. "Monday 10:00 AM EST"
    source_file: str            # Filename this was parsed from
    subreddit: Optional[str] = None
    flair: Optional[str] = None
    duration: Optional[str] = None       # e.g. "45 seconds"
    hashtags: list = field(default_factory=list)
    content_type: Optional[str] = None   # e.g. "Reel", "Carousel", "Educational"
    thread: list = field(default_factory=list)  # Twitter thread continuation tweets
    media_notes: Optional[str] = None    # Visual / production notes


# ══════════════════════════════════════════════════════════════
# Platform-Specific Parsers
# ══════════════════════════════════════════════════════════════

def parse_reddit_post(filepath: Path) -> SocialPost:
    """Parse a single Reddit post markdown file.

    Expected format (from reddit-week1-ready/postN-*.md):
      **Title:** ...
      **Target Subreddit:** ...
      **Best Time:** ...
      **Flair:** ...
      **Body:** ...
    """
    text = filepath.read_text()

    title = _extract_field(text, r'\*\*Title:\*\*\s*\n(.+)')
    target_sub = _extract_field(text, r'\*\*Target Subreddit:\*\*\s*(.+)')
    best_time = _extract_field(text, r'\*\*Best Time:\*\*\s*(.+)')
    flair = _extract_field(text, r'\*\*Flair:\*\*\s*(.+)')

    # Body: everything between **Body:** and the next --- or **IMPORTANT section
    body = ""
    m = re.search(r'\*\*Body:\*\*\s*\n(.+?)(?:\n---|\n\*\*IMPORTANT)', text, re.DOTALL)
    if m:
        body = m.group(1).strip()

    return SocialPost(
        platform="reddit",
        title=title,
        body=body,
        scheduled_time=best_time,
        source_file=filepath.name,
        subreddit=target_sub,
        flair=flair,
    )


def parse_tiktok_script(filepath: Path) -> SocialPost:
    """Parse a TikTok script markdown file.

    Expected format (from tiktok-week1-drafts/scriptN-*.md):
      **Video Title:** ...
      **Duration:** ...
      **Best Post Time:** ...
      **Type:** ...
      ## CAPTION ... ## HASHTAGS ...
    """
    text = filepath.read_text()

    title = _extract_field(text, r'\*\*Video Title:\*\*\s*"?(.+?)"?\s*\n')
    duration = _extract_field(text, r'\*\*Duration:\*\*\s*(\d+\s*seconds?)')
    best_time = _extract_field(text, r'\*\*Best Post Time:\*\*\s*(.+)')
    content_type = _extract_field(text, r'\*\*Type:\*\*\s*(.+)')

    # Caption block
    caption = ""
    m = re.search(r'## CAPTION.*?\n\n(.+?)(?:\n\n---|\n\n##)', text, re.DOTALL)
    if m:
        caption = m.group(1).strip()

    # Hashtags block
    hashtags = []
    m = re.search(r'## HASHTAGS\n\n(.+?)(?:\n\n---|\n\n##)', text, re.DOTALL)
    if m:
        raw = m.group(1).strip()
        hashtags = [t.strip() for t in raw.replace('\n', ' ').split() if t.strip().startswith('#')]

    return SocialPost(
        platform="tiktok",
        title=title,
        body=caption,
        scheduled_time=best_time,
        source_file=filepath.name,
        duration=duration,
        hashtags=hashtags,
        content_type=content_type,
    )


def parse_twitter_content(filepath: Path) -> list[SocialPost]:
    """Parse the Twitter/X content markdown file.

    Expected format (content/twitter-week1.md):
      ## Tweet N — "Topic Title"
      **Post Date:** Day, HH:MM AM/PM EST
      **Main Tweet (≤280 chars):** ```...```
      **Thread (N tweets):** ... ```...```
    """
    text = filepath.read_text()
    posts = []

    # Split into per-tweet sections
    sections = re.split(r'\n## Tweet \d+ —', text)
    if not sections or len(sections) < 2:
        return posts

    for section in sections[1:]:  # skip preamble
        # Title (quoted after the em-dash)
        title = ""
        m = re.match(r'\s*"(.+?)"', section)
        if m:
            title = m.group(1).strip()

        post_date = _extract_field(section, r'\*\*Post Date:\*\*\s*(.+)')
        tone = _extract_field(section, r'\*\*Tone:\*\*\s*(.+)')

        # Main tweet body (code block)
        main_tweet = ""
        m = re.search(r'\*\*Main Tweet.*?:\*\*\s*\n```\n(.+?)```', section, re.DOTALL)
        if m:
            main_tweet = m.group(1).strip()

        # Thread continuation tweets — two possible formats:
        # Format A: "Tweet 2:\n```...```" (explicit labels)
        # Format B: "**Thread (N tweets):**\n```...```" (thread text directly in block)
        thread = []
        for tm in re.finditer(r'Tweet (\d+):\s*\n```\n(.+?)```', section, re.DOTALL):
            thread.append(tm.group(2).strip())

        # If no labeled tweets found, try the inline format
        if not thread:
            m = re.search(r'\*\*Thread.*?:\*\*\s*\n```\n(.+?)```', section, re.DOTALL)
            if m:
                thread = [m.group(1).strip()]

        # Hashtags
        hashtags = []
        h = _extract_field(section, r'\*\*Hashtags:\*\*\s*(.+)')
        if h:
            hashtags = [tag.strip() for tag in h.split()]

        if main_tweet:
            posts.append(SocialPost(
                platform="twitter",
                title=title,
                body=main_tweet,
                scheduled_time=post_date,
                source_file=filepath.name,
                thread=thread,
                hashtags=hashtags,
                content_type=tone,
            ))

    return posts


def parse_master_file(filepath: Path, platforms: Optional[list[str]] = None) -> list[SocialPost]:
    """Parse week1-social-content.md for Instagram and Pinterest content.

    Extracts Instagram posts (### IG Post N) and Pinterest pins (### Pin N),
    plus the publishing calendar table for scheduled times.
    """
    text = filepath.read_text()
    posts = []

    # --- Parse the calendar table for schedule data ---
    calendar = _parse_calendar_table(text)

    # --- Instagram posts ---
    for m in re.finditer(r'### IG Post (\d+):.*?—\s*"(.+?)"', text):
        post_num = m.group(1)
        post_title = m.group(2).strip()

        section_start = m.start()
        section = text[section_start: section_start + 6000]

        # Content type (Reel / Carousel)
        ctype = _extract_field(section, r'\*\*类型:\*\*\s*(.+?)(?:\n|$)')
        if not ctype:
            ctype_m = re.search(r'\*\*类型:\*\*\s*(.+?)(?:\n|$)', section)
            if ctype_m:
                ctype = ctype_m.group(1).strip()

        # Caption (code block)
        caption = ""
        cm = re.search(r'\*\*Caption:\*\*\s*\n```\n(.+?)```', section, re.DOTALL)
        if cm:
            caption = cm.group(1).strip()

        # Scheduled time from calendar, or a default
        sched = _lookup_calendar(calendar, "Instagram", post_num)

        posts.append(SocialPost(
            platform="instagram",
            title=post_title,
            body=caption,
            scheduled_time=sched or "TBD",
            source_file=filepath.name,
            content_type=ctype,
        ))

    # --- Pinterest pins ---
    for m in re.finditer(r'### Pin (\d+):\s+"(.+?)"', text):
        pin_num = m.group(1)
        pin_title_chinese = m.group(2).strip()

        section_start = m.start()
        section = text[section_start: section_start + 5000]

        # English pin title
        en_title = _extract_field(section, r'\*\*图钉标题.*?:\*\*\s*\n(.+)')

        # Pin description
        desc = ""
        dm = re.search(r'\*\*图钉描述.*?:\*\*\s*\n(.+?)(?:\n\n#|\n\n\*\*)', section, re.DOTALL)
        if dm:
            desc = dm.group(1).strip()

        sched = _lookup_calendar(calendar, "Pinterest", pin_num)

        posts.append(SocialPost(
            platform="pinterest",
            title=en_title or pin_title_chinese,
            body=desc,
            scheduled_time=sched or "TBD",
            source_file=filepath.name,
            content_type="Pin",
        ))

    # Filter by platform if requested
    if platforms:
        posts = [p for p in posts if p.platform in platforms]

    return posts


# ══════════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════════

def _extract_field(text: str, pattern: str) -> str:
    """Extract a single field via regex. Returns empty string on no match."""
    m = re.search(pattern, text)
    return m.group(1).strip() if m else ""


def _parse_calendar_table(text: str) -> list[dict]:
    """Parse the markdown calendar table into a list of {platform, day, time, content} dicts."""
    rows = []
    in_table = False

    for line in text.split('\n'):
        if '日期' in line and '平台' in line and '时间' in line:
            in_table = True
            continue
        if in_table:
            if line.strip().startswith('|---'):
                continue
            if line.strip().startswith('|'):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 4:
                    rows.append({
                        "day": parts[0],
                        "platform": parts[1],
                        "content": parts[2],
                        "time": parts[3],
                    })
            elif not line.strip().startswith('|'):
                in_table = False

    return rows


def _lookup_calendar(calendar: list[dict], platform: str, post_num: str) -> Optional[str]:
    """Find a scheduled time in the calendar for a given platform and post number.

    Matches by counting occurrences of the platform name in the calendar.
    Post 1 = first occurrence, Post 2 = second, etc.
    """
    count = 0
    target = int(post_num)

    for row in calendar:
        if platform.lower() in row["platform"].lower():
            count += 1
            if count == target:
                return f"{row['day']} {row['time']} EST"

    return None


def _day_sort_key(scheduled_time: str) -> int:
    """Extract a numeric sort key from a scheduled time string."""
    day_map = {
        "monday": 1, "tuesday": 2, "wednesday": 3,
        "thursday": 4, "friday": 5, "saturday": 6, "sunday": 7,
    }
    prefix = scheduled_time.lower().split()[0] if scheduled_time else ""
    return day_map.get(prefix, 9)


def _time_sort_key(scheduled_time: str) -> int:
    """Extract hour (0-23) from scheduled time for tie-breaking."""
    m = re.search(r'(\d{1,2}):(\d{2})', scheduled_time)
    if not m:
        return 0
    hour = int(m.group(1))
    if 'PM' in scheduled_time.upper() and hour != 12:
        hour += 12
    if 'AM' in scheduled_time.upper() and hour == 12:
        hour = 0
    return hour


# ══════════════════════════════════════════════════════════════
# Main Scheduler
# ══════════════════════════════════════════════════════════════

PLATFORM_ORDER = {"instagram": 0, "tiktok": 1, "twitter": 2, "reddit": 3, "pinterest": 4}


def build_schedule(project_dir: str, platforms: Optional[list[str]] = None) -> dict:
    """Build the complete content schedule from all sources in the project directory.

    Args:
        project_dir: Path to the metaphysics-landing project root.
        platforms: Optional list of platforms to include. None = all.

    Returns:
        A dict with keys: generated_at, project, week, total_posts, platforms, posts.
    """
    root = Path(project_dir)
    content: list[SocialPost] = []

    def _include(plat: str) -> bool:
        return platforms is None or plat in platforms

    # ── Reddit posts ──
    reddit_dir = root / "reddit-week1-ready"
    if reddit_dir.exists() and _include("reddit"):
        for f in sorted(reddit_dir.glob("*.md")):
            try:
                content.append(parse_reddit_post(f))
            except Exception as e:
                print(f"⚠️  Failed to parse {f.name}: {e}", file=sys.stderr)

    # ── TikTok scripts ──
    tiktok_dir = root / "tiktok-week1-drafts"
    if tiktok_dir.exists() and _include("tiktok"):
        for f in sorted(tiktok_dir.glob("*.md")):
            try:
                content.append(parse_tiktok_script(f))
            except Exception as e:
                print(f"⚠️  Failed to parse {f.name}: {e}", file=sys.stderr)

    # ── Twitter content ──
    twitter_file = root / "content" / "twitter-week1.md"
    if twitter_file.exists() and _include("twitter"):
        try:
            content.extend(parse_twitter_content(twitter_file))
        except Exception as e:
            print(f"⚠️  Failed to parse twitter-week1.md: {e}", file=sys.stderr)

    # ── Master file (Instagram + Pinterest) ──
    master_file = root / "week1-social-content.md"
    if master_file.exists():
        wanted = None
        if platforms:
            wanted = [p for p in platforms if p in ("instagram", "pinterest")]
            if not wanted:
                wanted = None  # don't parse if neither is wanted
        if wanted is not False:
            try:
                content.extend(parse_master_file(master_file, platforms))
            except Exception as e:
                print(f"⚠️  Failed to parse {master_file.name}: {e}", file=sys.stderr)

    # ── Sort: by day → time → platform ──
    def sort_key(post: SocialPost):
        return (
            _day_sort_key(post.scheduled_time),
            _time_sort_key(post.scheduled_time),
            PLATFORM_ORDER.get(post.platform, 9),
        )

    content.sort(key=sort_key)

    # ── Build output ──
    schedule = {
        "generated_at": datetime.now().isoformat(),
        "project": "Destiny Code",
        "week": 1,
        "total_posts": len(content),
        "platforms": platforms or ["reddit", "tiktok", "twitter", "instagram", "pinterest"],
        "posts": [asdict(p) for p in content],
    }
    return schedule


# ══════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Destiny Code — Social Media Content Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # All platforms → stdout
  %(prog)s --platform twitter                 # Twitter/X only
  %(prog)s -p reddit -p tiktok                # Reddit + TikTok
  %(prog)s --dry-run                          # Validate only, no JSON output
  %(prog)s -o schedule.json                   # Write JSON to file
        """,
    )
    parser.add_argument(
        "--platform", "-p",
        action="append",
        dest="platforms",
        choices=["reddit", "tiktok", "twitter", "instagram", "pinterest"],
        help="Filter to specific platform(s). Repeat for multiple. Default: all.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate all content but do not output JSON. Prints summary.",
    )
    parser.add_argument(
        "--output", "-o",
        help="Write JSON schedule to file instead of stdout.",
    )

    args = parser.parse_args()

    # Determine project root (scripts/ → parent)
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent

    schedule = build_schedule(str(project_dir), args.platforms)

    if args.dry_run:
        plat_list = ", ".join(schedule["platforms"])
        print(f"✅ Dry run successful — {schedule['total_posts']} posts across: {plat_list}\n")
        for post in schedule["posts"]:
            sched = post["scheduled_time"][:35].ljust(35)
            plat = f"[{post['platform']:10s}]"
            title = post["title"][:60]
            print(f"  {plat} {sched} | {title}")
        return

    json_str = json.dumps(schedule, indent=2, ensure_ascii=False)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json_str)
        print(f"✅ Schedule written to {output_path} ({schedule['total_posts']} posts)")
    else:
        print(json_str)


if __name__ == "__main__":
    main()
