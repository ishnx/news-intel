#!/usr/bin/env python3
"""
rank_news.py - Intelligence Ranking Engine
==========================================
Reads articles from staging/raw/ and scores them for strategic importance.
The top N stories proceed to deep analysis.

RUN: python scripts/rank_news.py
INPUT: staging/raw/YYYY-MM-DD/articles.json
OUTPUT: staging/ranked/YYYY-MM-DD/ranked_articles.json
NEXT: scripts/analyze_story.py
"""

import json
import os
import sys
import re
import yaml
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# CONFIGURATION LOADING
# ============================================================

def load_topic_weights():
    """Load topic keyword weights from config/topic_weights.json."""
    path = PROJECT_ROOT / "config" / "topic_weights.json"
    with open(path) as f:
        data = json.load(f)
    return data.get("topics", {})


def load_source_weights():
    """Load source trust weights from config/source_weights.json."""
    path = PROJECT_ROOT / "config" / "source_weights.json"
    with open(path) as f:
        data = json.load(f)
    return data.get("source_weights", {}), data.get("domain_trust", {})


def load_entity_priorities():
    """Load entity priority lists from config/entity_priorities.json."""
    path = PROJECT_ROOT / "config" / "entity_priorities.json"
    with open(path) as f:
        data = json.load(f)
    return data


def load_schedules():
    """Load schedule config to get stories_per_run limit."""
    path = PROJECT_ROOT / "config" / "schedules.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


# ============================================================
# SCORING FUNCTIONS
# ============================================================

def score_source(article, source_weights, default_weight=0.8):
    """
    Score an article based on the trust/quality of its source.
    Returns a multiplier between 0.5 and 1.5.
    """
    source_name = article.get("source_name", "")

    # Check exact match first
    if source_name in source_weights:
        return source_weights[source_name]

    # Check partial matches (e.g., "Bloomberg Markets" matches "Bloomberg")
    for key, weight in source_weights.items():
        if key.lower() in source_name.lower() or source_name.lower() in key.lower():
            return weight

    # Use the weight set during fetch (from feeds.yaml trust field)
    if article.get("source_weight"):
        return article["source_weight"]

    return source_weights.get("default", default_weight)


def score_topics(article, topic_weights):
    """
    Score an article by how many high-priority topics it covers.
    Returns a base score (0-100) and a list of matched topics.
    """
    # Combine title and summary for matching
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    matched_topics = []
    topic_score = 0

    for topic_name, topic_data in topic_weights.items():
        weight = topic_data.get("weight", 1.0)
        keywords = [kw.lower() for kw in topic_data.get("keywords", [])]

        # Count how many keywords from this topic appear in the article
        matches = sum(1 for kw in keywords if kw in text)

        if matches > 0:
            # Score increases with matches but with diminishing returns
            contribution = weight * (1 + (matches - 1) * 0.3) * 10
            topic_score += contribution
            matched_topics.append({
                "topic": topic_name,
                "matches": matches,
                "contribution": contribution
            })

    # Cap at 80 for topic scoring (source quality and novelty also matter)
    return min(topic_score, 80), matched_topics


def score_entities(article, entity_priorities):
    """
    Boost score if the article mentions tracked priority entities.
    Returns an additive bonus.
    """
    text = (article.get("title", "") + " " + article.get("summary", "")).lower()
    bonus = 0

    # Priority 1 entities: +15 bonus each (max 2 matches = 30)
    p1_matches = 0
    for entities in entity_priorities.values():
        if isinstance(entities, dict):
            for priority, entity_list in entities.items():
                if priority == "priority_1" and isinstance(entity_list, list):
                    for entity in entity_list:
                        if entity.lower() in text:
                            p1_matches += 1

    bonus += min(p1_matches * 15, 30)

    # Priority 2 entities: +8 bonus each (max 2 matches = 16)
    p2_matches = 0
    for entities in entity_priorities.values():
        if isinstance(entities, dict):
            for priority, entity_list in entities.items():
                if priority == "priority_2" and isinstance(entity_list, list):
                    for entity in entity_list:
                        if entity.lower() in text:
                            p2_matches += 1

    bonus += min(p2_matches * 8, 16)

    return bonus


def score_intelligence_keywords(text):
    """
    Apply keyword-based intelligence boosts from intelligence_scoring.md logic.
    Returns an additive bonus.
    """
    text_lower = text.lower()
    bonus = 0

    # High-value signal keywords (+2 each)
    tier1_keywords = [
        "agi", "artificial general intelligence", "nuclear", "fusion",
        "taiwan", "invasion", "default", "sovereign debt crisis",
        "pandemic", "pathogen", "unprecedented", "paradigm shift"
    ]

    # Strategic keywords (+1 each)
    tier2_keywords = [
        "breakthrough", "sanctions", "export controls", "banned", "ban",
        "acquisition", "merger", "regulation", "law passed", "chip war",
        "arms race", "critical minerals", "supply chain", "strategic"
    ]

    # Noise reduction (subtract for low-signal patterns)
    noise_keywords = [
        "quarterly earnings beat", "stock split", "dividend declared",
        "routine maintenance", "scheduled", "as expected"
    ]

    for kw in tier1_keywords:
        if kw in text_lower:
            bonus += 2

    for kw in tier2_keywords:
        if kw in text_lower:
            bonus += 1

    for kw in noise_keywords:
        if kw in text_lower:
            bonus -= 2

    return bonus


def score_recency(article):
    """
    Give a small freshness bonus to very recent articles.
    Very old articles get a slight penalty.
    Returns a multiplier between 0.8 and 1.1.
    """
    try:
        pub_date_str = article.get("published_at", "")
        if not pub_date_str:
            return 1.0

        pub_date = datetime.fromisoformat(pub_date_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        age_hours = (now - pub_date).total_seconds() / 3600

        if age_hours < 3:
            return 1.1   # Very fresh
        elif age_hours < 8:
            return 1.05  # Recent
        elif age_hours < 16:
            return 1.0   # Normal
        elif age_hours < 24:
            return 0.95  # Getting older
        else:
            return 0.85  # Old news
    except Exception:
        return 1.0


def compute_novelty_penalty(article, recently_analyzed_titles):
    """
    Penalize articles very similar to recently analyzed stories.
    Prevents analyzing the same story twice.
    Returns a multiplier between 0.3 and 1.0.
    """
    def get_word_set(title):
        words = set(re.sub(r'[^a-z0-9\s]', '', title.lower()).split())
        stops = {'the', 'a', 'an', 'is', 'in', 'on', 'at', 'to', 'of', 'and', 'or', 'for', 'by'}
        return words - stops

    current_words = get_word_set(article.get("title", ""))
    if not current_words:
        return 1.0

    for analyzed_title in recently_analyzed_titles:
        analyzed_words = get_word_set(analyzed_title)
        if not analyzed_words:
            continue
        overlap = len(current_words & analyzed_words)
        union = len(current_words | analyzed_words)
        similarity = overlap / union if union > 0 else 0

        if similarity > 0.6:
            return 0.3  # Strong penalty for near-duplicates of recent analysis
        elif similarity > 0.4:
            return 0.7  # Moderate penalty

    return 1.0


# ============================================================
# MAIN SCORING PIPELINE
# ============================================================

def score_article(article, topic_weights, source_weights, entity_priorities,
                  recently_analyzed_titles):
    """
    Compute the final intelligence score for an article.

    Score components:
    - Topic relevance (0-80): Does this cover high-priority topics?
    - Source quality (multiplier): How trustworthy is the source?
    - Entity priority (0-30 bonus): Does it mention tracked entities?
    - Intelligence keywords (additive bonus): Does it signal strategic importance?
    - Recency (multiplier): How fresh is it?
    - Novelty (multiplier): Is it genuinely new vs. recently covered?

    Final score range: approximately 0-100
    """
    text = article.get("title", "") + " " + article.get("summary", "")

    # Component scores
    topic_score, matched_topics = score_topics(article, topic_weights)
    source_multiplier = score_source(article, source_weights)
    entity_bonus = score_entities(article, entity_priorities)
    keyword_bonus = score_intelligence_keywords(text)
    recency_multiplier = score_recency(article)
    novelty_multiplier = compute_novelty_penalty(article, recently_analyzed_titles)

    # Also apply the category weight set during fetch
    category_weight = article.get("category_weight", 1.0)

    # Final formula
    raw_score = (topic_score * source_multiplier * category_weight
                 + entity_bonus
                 + keyword_bonus)

    final_score = raw_score * recency_multiplier * novelty_multiplier

    # Store scoring breakdown for transparency
    article["intelligence_score"] = round(final_score, 2)
    article["score_breakdown"] = {
        "topic_score": round(topic_score, 2),
        "source_multiplier": round(source_multiplier, 2),
        "entity_bonus": entity_bonus,
        "keyword_bonus": keyword_bonus,
        "recency_multiplier": round(recency_multiplier, 2),
        "novelty_multiplier": round(novelty_multiplier, 2),
        "category_weight": category_weight,
        "matched_topics": [t["topic"] for t in matched_topics[:5]]
    }

    return article


def load_recently_analyzed_titles(days_back=7):
    """
    Load titles of stories analyzed in the last N days.
    Used to avoid re-analyzing the same story.
    """
    titles = []
    now = datetime.now(timezone.utc)

    for day_offset in range(days_back):
        date = (now - timedelta(days=day_offset)).strftime("%Y-%m-%d")
        reports_dir = PROJECT_ROOT / "reports" / date[:4] / date[5:7] / date[8:]

        if not reports_dir.exists():
            continue

        for story_dir in reports_dir.iterdir():
            if story_dir.is_dir():
                data_file = story_dir / "structured_data.json"
                if data_file.exists():
                    try:
                        with open(data_file) as f:
                            data = json.load(f)
                        titles.append(data.get("metadata", {}).get("title", ""))
                    except Exception:
                        pass

    return titles


# ============================================================
# LOAD AND RANK
# ============================================================

def load_todays_articles():
    """Load today's fetched articles from staging."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = PROJECT_ROOT / "staging" / "raw" / today / "articles.json"

    if not path.exists():
        print(f"ERROR: No articles file found at {path}")
        print("Run fetch_news.py first!")
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    return data.get("articles", []), data.get("metadata", {})


def rank_and_save(articles, top_n, metadata):
    """
    Score all articles, rank them, and save the top N.
    """
    topic_weights = load_topic_weights()
    source_weights_dict, _ = load_source_weights()
    entity_priorities = load_entity_priorities()
    recently_analyzed = load_recently_analyzed_titles()

    print(f"\n  Scoring {len(articles)} articles...")
    print(f"  Avoiding re-analysis of {len(recently_analyzed)} recent stories")

    # Score all articles
    scored_articles = []
    for article in articles:
        scored = score_article(
            article,
            topic_weights,
            source_weights_dict,
            entity_priorities,
            recently_analyzed
        )
        scored_articles.append(scored)

    # Sort by score (highest first)
    scored_articles.sort(key=lambda a: a.get("intelligence_score", 0), reverse=True)

    # Assign ranks
    for i, article in enumerate(scored_articles):
        article["rank"] = i + 1

    # Print top 10 for transparency
    print(f"\n  Top stories by intelligence score:")
    for article in scored_articles[:10]:
        score = article.get("intelligence_score", 0)
        topics = article.get("score_breakdown", {}).get("matched_topics", [])
        topics_str = ", ".join(topics[:3]) if topics else "general"
        print(f"    #{article['rank']:2d} [{score:5.1f}] {article['title'][:70]}")
        print(f"           Source: {article['source_name']} | Topics: {topics_str}")

    print(f"\n  Top {top_n} will proceed to deep analysis")

    # Save all ranked articles
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_dir = PROJECT_ROOT / "staging" / "ranked" / today
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "ranked_articles.json"
    with open(output_path, "w") as f:
        json.dump({
            "metadata": {
                **metadata,
                "ranked_at": datetime.now(timezone.utc).isoformat(),
                "total_ranked": len(scored_articles),
                "top_n": top_n
            },
            "articles": scored_articles
        }, f, indent=2)

    # Save just the top N for analysis
    top_path = output_dir / "top_stories.json"
    with open(top_path, "w") as f:
        json.dump({
            "metadata": {
                "date": today,
                "top_n": top_n,
                "selected_at": datetime.now(timezone.utc).isoformat()
            },
            "stories": scored_articles[:top_n]
        }, f, indent=2)

    print(f"\n  Saved ranked list to {output_path.relative_to(PROJECT_ROOT)}")
    print(f"  Saved top {top_n} to {top_path.relative_to(PROJECT_ROOT)}")

    return scored_articles[:top_n]


# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "="*60)
    print("STEP 2: RANKING NEWS BY INTELLIGENCE VALUE")
    print("="*60)

    schedules = load_schedules()
    top_n = schedules.get("stories_per_run", 5)

    articles, metadata = load_todays_articles()
    print(f"\n  Loaded {len(articles)} articles from today's fetch")

    if not articles:
        print("  No articles to rank. Exiting.")
        return

    top_stories = rank_and_save(articles, top_n, metadata)

    print("\n" + "="*60)
    print(f"✓ STEP 2 COMPLETE: Top {len(top_stories)} stories selected")
    print("="*60)


if __name__ == "__main__":
    main()
