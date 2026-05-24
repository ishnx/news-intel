#!/usr/bin/env python3
"""
fetch_news.py - News Ingestion Engine
======================================
Fetches articles from RSS feeds configured in config/feeds.yaml.
Saves raw articles as JSON for the ranking step.

RUN: python scripts/fetch_news.py
OUTPUT: staging/raw/YYYY-MM-DD/articles.json
NEXT: scripts/rank_news.py
"""

import feedparser
import json
import os
import sys
import yaml
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add project root to path so we can import from anywhere
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dateutil import parser as dateparser
    HAS_DATEUTIL = True
except ImportError:
    HAS_DATEUTIL = False
    print("WARNING: python-dateutil not installed. Date parsing may be less reliable.")


# ============================================================
# CONFIGURATION
# ============================================================

def load_feeds_config():
    """Load the feeds configuration from config/feeds.yaml."""
    config_path = PROJECT_ROOT / "config" / "feeds.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def load_schedules_config():
    """Load schedule settings from config/schedules.yaml."""
    config_path = PROJECT_ROOT / "config" / "schedules.yaml"
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_cutoff_time(schedules_config):
    """
    Calculate how far back to look for articles.
    Returns a timezone-aware datetime for the cutoff.
    """
    hours = schedules_config.get("fetch_window_hours", 24)
    return datetime.now(timezone.utc) - timedelta(hours=hours)


# ============================================================
# DATE PARSING
# ============================================================

def parse_date(entry):
    """
    Try multiple methods to extract a publication date from a feed entry.
    Returns a timezone-aware datetime, or 'now' if nothing can be parsed.
    """
    # Method 1: feedparser's parsed tuple (most reliable)
    for attr in ['published_parsed', 'updated_parsed', 'created_parsed']:
        val = getattr(entry, attr, None)
        if val:
            try:
                return datetime(*val[:6], tzinfo=timezone.utc)
            except (TypeError, ValueError):
                pass

    # Method 2: raw string via dateutil (handles many formats)
    if HAS_DATEUTIL:
        for attr in ['published', 'updated', 'created']:
            val = getattr(entry, attr, None)
            if val:
                try:
                    dt = dateparser.parse(val)
                    if dt and dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    return dt
                except Exception:
                    pass

    # Fallback: assume now (article will be included but may be old)
    return datetime.now(timezone.utc)


# ============================================================
# ARTICLE EXTRACTION
# ============================================================

def extract_article(entry, feed_name, feed_url, category, source_weight):
    """
    Extract a clean article dictionary from a feedparser entry.

    We store a fingerprint (hash of the URL) as the ID so we can
    easily deduplicate across runs.
    """
    url = entry.get("link", "").strip()
    if not url:
        return None  # Skip entries without URLs

    # Clean up the summary/content
    summary = ""
    if hasattr(entry, 'summary') and entry.summary:
        summary = entry.summary
    elif hasattr(entry, 'description') and entry.description:
        summary = entry.description
    elif hasattr(entry, 'content') and entry.content and len(entry.content) > 0:
        summary = entry.content[0].get('value', '')

    # Strip HTML tags (basic, without BeautifulSoup dependency)
    # BeautifulSoup is optional — it does a better job but isn't required
    try:
        from bs4 import BeautifulSoup
        summary = BeautifulSoup(summary, 'html.parser').get_text(separator=' ')
    except ImportError:
        # Fallback: crude HTML stripping
        import re
        summary = re.sub(r'<[^>]+>', ' ', summary)
        summary = re.sub(r'\s+', ' ', summary).strip()

    summary = summary[:3000]  # Cap at 3000 chars to control token usage later

    pub_date = parse_date(entry)

    return {
        # Unique identifier: hash of URL (stable across re-fetches)
        "id": hashlib.md5(url.encode()).hexdigest()[:16],
        "title": entry.get("title", "No Title").strip(),
        "url": url,
        "summary": summary,
        "published_at": pub_date.isoformat(),
        "source_name": feed_name,
        "source_url": feed_url,
        "category": category,
        "source_weight": source_weight,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        # Will be populated by rank_news.py
        "intelligence_score": 0,
        "rank": 0
    }


# ============================================================
# FEED FETCHING
# ============================================================

def fetch_single_feed(feed_config, category, cutoff_time, max_per_feed, min_length):
    """
    Fetch a single RSS feed and return qualifying articles.

    Handles network errors gracefully — a failing feed never crashes
    the whole pipeline.
    """
    feed_url = feed_config.get("url", "")
    feed_name = feed_config.get("name", "Unknown")
    source_weight = feed_config.get("trust", 0.8)
    articles = []

    if not feed_url:
        return articles

    try:
        print(f"    Fetching: {feed_name}")

        # feedparser handles HTTP, redirects, encoding, etc.
        feed = feedparser.parse(feed_url)

        if feed.bozo and not feed.entries:
            # bozo=True means the feed had parsing issues
            print(f"      WARNING: Feed parsing issues for {feed_name}: {feed.bozo_exception}")

        count = 0
        for entry in feed.entries:
            if count >= max_per_feed:
                break

            pub_date = parse_date(entry)

            # Skip articles older than our cutoff window
            if pub_date < cutoff_time:
                continue

            article = extract_article(entry, feed_name, feed_url, category, source_weight)

            if article is None:
                continue

            # Skip articles with very short summaries (likely stubs)
            if len(article["summary"]) < min_length:
                continue

            articles.append(article)
            count += 1

        print(f"      Found {len(articles)} qualifying articles")

    except Exception as e:
        # Log but don't crash — one bad feed shouldn't stop the whole run
        print(f"      ERROR fetching {feed_name}: {type(e).__name__}: {e}")

    return articles


def fetch_all_feeds(feeds_config, schedules_config, cutoff_time):
    """
    Iterate through all feed groups and fetch articles from each source.
    Returns a flat list of all articles.
    """
    max_per_feed = feeds_config.get("max_articles_per_feed", 20)
    min_length = feeds_config.get("min_summary_length", 100)
    all_articles = []

    for feed_group in feeds_config.get("feeds", []):
        category = feed_group.get("category", "general")
        category_weight = feed_group.get("weight", 1.0)
        sources = feed_group.get("sources", [])

        print(f"\n  [{category.upper()}] — {len(sources)} sources")

        for source in sources:
            articles = fetch_single_feed(
                feed_config=source,
                category=category,
                cutoff_time=cutoff_time,
                max_per_feed=max_per_feed,
                min_length=min_length
            )
            # Apply category weight to each article's base score
            for a in articles:
                a["category_weight"] = category_weight
            all_articles.extend(articles)

    return all_articles


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate_articles(articles):
    """
    Remove duplicate articles.
    When duplicates exist (same URL), keep the one with the most content.
    Also attempts rough title-based dedup for syndicated content.
    """
    # Pass 1: URL-based exact dedup
    seen_urls = {}
    for article in articles:
        url = article["url"]
        if url not in seen_urls:
            seen_urls[url] = article
        else:
            # Keep the longer summary
            if len(article["summary"]) > len(seen_urls[url]["summary"]):
                seen_urls[url] = article

    unique_articles = list(seen_urls.values())

    # Pass 2: Title-based approximate dedup (catches same story across syndication)
    import re

    def normalize_title(title):
        """Reduce title to core words for comparison."""
        t = title.lower()
        t = re.sub(r'[^a-z0-9\s]', '', t)
        words = set(t.split())
        # Remove common stop words
        stops = {'the', 'a', 'an', 'is', 'in', 'on', 'at', 'to', 'of', 'and', 'or', 'for'}
        return words - stops

    seen_titles = {}
    final_articles = []

    for article in unique_articles:
        norm_title = frozenset(normalize_title(article["title"]))
        if not norm_title:
            final_articles.append(article)
            continue

        # Check if we've seen a very similar title (>70% word overlap)
        is_duplicate = False
        for seen_norm, seen_article in seen_titles.items():
            if len(norm_title) == 0 or len(seen_norm) == 0:
                continue
            intersection = len(norm_title & seen_norm)
            union = len(norm_title | seen_norm)
            similarity = intersection / union if union > 0 else 0

            if similarity > 0.7:
                # Keep the one from the more trusted source
                if article.get("source_weight", 0) > seen_article.get("source_weight", 0):
                    # Replace with the better source
                    final_articles.remove(seen_article)
                    final_articles.append(article)
                    seen_titles[frozenset(normalize_title(article["title"]))] = article
                is_duplicate = True
                break

        if not is_duplicate:
            final_articles.append(article)
            seen_titles[norm_title] = article

    return final_articles


# ============================================================
# PERSISTENCE
# ============================================================

def save_articles(articles, cutoff_time):
    """
    Save fetched articles to staging/raw/YYYY-MM-DD/articles.json.
    Creates directories as needed.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_dir = PROJECT_ROOT / "staging" / "raw" / today
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "articles.json"

    # Sort by publication date (newest first) for readability
    articles.sort(key=lambda a: a.get("published_at", ""), reverse=True)

    payload = {
        "metadata": {
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "cutoff_time": cutoff_time.isoformat(),
            "total_articles": len(articles),
            "date": today
        },
        "articles": articles
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved {len(articles)} articles to {output_path.relative_to(PROJECT_ROOT)}")
    return output_path


def load_existing_articles():
    """
    Load today's existing articles if fetch is being re-run.
    Returns empty list if none exist yet.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = PROJECT_ROOT / "staging" / "raw" / today / "articles.json"
    if path.exists():
        with open(path) as f:
            data = json.load(f)
        return data.get("articles", [])
    return []


# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "="*60)
    print("STEP 1: FETCHING NEWS FEEDS")
    print("="*60)

    feeds_config = load_feeds_config()
    schedules_config = load_schedules_config()
    cutoff_time = get_cutoff_time(schedules_config)

    print(f"\nFetch window: last {schedules_config.get('fetch_window_hours', 24)} hours")
    print(f"Cutoff time:  {cutoff_time.strftime('%Y-%m-%d %H:%M UTC')}")

    # Check for priority overrides (manual additions)
    override_path = PROJECT_ROOT / "staging" / "priority_override.json"
    override_articles = []
    if override_path.exists():
        with open(override_path) as f:
            override_data = json.load(f)
        overrides = override_data.get("force_analyze", [])
        for item in overrides:
            override_articles.append({
                "id": hashlib.md5(item.get("url", "").encode()).hexdigest()[:16],
                "title": item.get("title", "Manual Override"),
                "url": item.get("url", ""),
                "summary": item.get("reason", "Manually queued for analysis"),
                "published_at": datetime.now(timezone.utc).isoformat(),
                "source_name": item.get("source", "manual"),
                "source_url": "",
                "category": "manual",
                "source_weight": 2.0,  # Priority overrides always get analyzed
                "category_weight": 2.0,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "intelligence_score": 100,
                "rank": 0
            })
        if override_articles:
            print(f"\n  Found {len(override_articles)} priority override(s)")

    print("\nFetching feeds...")
    all_articles = fetch_all_feeds(feeds_config, schedules_config, cutoff_time)
    all_articles.extend(override_articles)

    print(f"\nRaw articles fetched: {len(all_articles)}")

    # Deduplicate
    all_articles = deduplicate_articles(all_articles)
    print(f"After deduplication: {len(all_articles)}")

    # Save to staging
    save_articles(all_articles, cutoff_time)

    print("\n" + "="*60)
    print("✓ STEP 1 COMPLETE: News fetch done")
    print("="*60)


if __name__ == "__main__":
    main()
