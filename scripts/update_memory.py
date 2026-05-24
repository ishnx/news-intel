#!/usr/bin/env python3
"""
update_memory.py - Memory and World Model Evolution Engine
==========================================================
Reads memory_updates.md from each analyzed story and applies
the updates to the persistent memory files.

This is what makes the system compound — each analysis permanently
enriches the knowledge base that future analyses draw from.

RUN: python scripts/update_memory.py
INPUT: reports/YYYY/MM/DD/*/memory_updates.md
OUTPUT: Updated memory/ files, updated world_model/ files
NEXT: scripts/build_indexes.py
"""

import json
import os
import re
import sys
import yaml
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# HELPERS
# ============================================================

def append_to_memory_file(file_path, content, section_header=None):
    """
    Append content to a memory markdown file.
    Creates the file if it doesn't exist.
    If section_header is provided, content is added under that section.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if section_header:
        entry = f"\n### {timestamp}: {section_header}\n{content}\n"
    else:
        entry = f"\n- **{timestamp}**: {content}\n"

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(entry)


def update_entity_file(entity_name, entity_type, update_text, source_story=""):
    """
    Update or create an entity file in world_model/.
    Entity files accumulate knowledge about specific people, companies, etc.
    """
    # Sanitize entity name for use as filename
    safe_name = re.sub(r'[^a-z0-9-]', '-', entity_name.lower())
    safe_name = re.sub(r'-+', '-', safe_name).strip('-')

    # Determine the subdirectory based on entity type
    type_to_dir = {
        "person": "people",
        "company": "companies",
        "country": "countries",
        "technology": "technologies",
        "institution": "entities",
        "theme": "themes",
        "default": "entities"
    }

    subdir = type_to_dir.get(entity_type.lower(), "entities")
    entity_file = PROJECT_ROOT / "world_model" / subdir / f"{safe_name}.md"

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if not entity_file.exists():
        # Create new entity file
        content = f"""# {entity_name}
**Type:** {entity_type}
**First Tracked:** {timestamp}

## Overview
*(Auto-created entity — add description here)*

## Timeline of Developments

### {timestamp}
{update_text}
*Source: {source_story}*

"""
    else:
        # Append to existing entity file
        with open(entity_file) as f:
            existing = f.read()

        # Add to timeline
        content = existing + f"\n### {timestamp}\n{update_text}\n*Source: {source_story}*\n"

    with open(entity_file, "w") as f:
        f.write(content)

    return entity_file


def update_thesis(thesis_name, update_text, action, source_story=""):
    """
    Update an active thesis in memory/active_theses.md.
    Actions: strengthen, weaken, new, close
    """
    theses_file = PROJECT_ROOT / "memory" / "active_theses.md"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    entry = f"""
#### {timestamp} — {action.upper()} [{source_story}]
{update_text}
"""

    if action == "new":
        # Add as a new thesis
        new_thesis_section = f"""
---

## {thesis_name}
**Status:** Active | **Opened:** {timestamp}
**Conviction:** Medium (newly established)

### Evidence Log
{entry}
"""
        with open(theses_file, "a") as f:
            f.write(new_thesis_section)

    elif action == "close":
        # Mark thesis as closed (resolved/invalidated)
        with open(theses_file) as f:
            content = f.read()
        content = content.replace(
            f"## {thesis_name}\n**Status:** Active",
            f"## {thesis_name}\n**Status:** CLOSED ({timestamp})"
        )
        content += f"\n### CLOSED {timestamp}\n{update_text}\n*Source: {source_story}*\n"
        with open(theses_file, "w") as f:
            f.write(content)

    else:
        # strengthen or weaken — append to existing thesis
        with open(theses_file, "a") as f:
            f.write(f"\n**Thesis: {thesis_name}**{entry}")


def update_pattern(pattern_name, observation, source_story=""):
    """
    Update a recurring pattern in memory/recurring_patterns.md.
    If the pattern is new, creates it. If existing, increments count.
    """
    patterns_file = PROJECT_ROOT / "memory" / "recurring_patterns.md"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if not patterns_file.exists():
        return

    with open(patterns_file) as f:
        content = f.read()

    # Check if pattern already exists
    if f"## {pattern_name}" in content:
        # Find and update the count
        count_match = re.search(rf'## {re.escape(pattern_name)}.*?Count:\*\* (\d+)', content, re.DOTALL)
        if count_match:
            old_count = int(count_match.group(1))
            content = content.replace(
                f"**Count:** {old_count}",
                f"**Count:** {old_count + 1}",
                1  # Only replace first occurrence in this pattern's section
            )

        # Append observation
        content += f"""
### {timestamp} — Instance #{source_story}
{observation}
"""
        with open(patterns_file, "w") as f:
            f.write(content)
    else:
        # New pattern
        new_pattern = f"""
---

## {pattern_name}
**First Observed:** {timestamp}
**Count:** 1
**Status:** Emerging

### Description
*(Auto-generated pattern — review and refine this description)*

### {timestamp} — First Instance
{observation}
*Source: {source_story}*
"""
        with open(patterns_file, "a") as f:
            f.write(new_pattern)


def ensure_memory_file(file_path, title, description=""):
    """
    Ensure a memory file exists. Creates it with a header if it doesn't.
    This makes all memory-writing functions safe even on a fresh install.
    """
    path = Path(file_path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(f"# {title}\n\n{description}\n\n")


def add_unresolved_question(question, source_story=""):
    """Add a new question to memory/unresolved_questions.md."""
    questions_file = PROJECT_ROOT / "memory" / "unresolved_questions.md"
    ensure_memory_file(questions_file, "Unresolved Questions",
                       "Open intelligence questions awaiting resolution.")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    entry = f"- **{timestamp}** [{source_story}]: {question}\n"

    with open(questions_file, "a") as f:
        f.write(entry)


def add_master_memory(insight, source_story=""):
    """Add a new insight to memory/master_memory.md."""
    memory_file = PROJECT_ROOT / "memory" / "master_memory.md"
    ensure_memory_file(memory_file, "Master Memory",
                       "Accumulated intelligence facts and insights.")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    entry = f"- **{timestamp}** [{source_story}]: {insight}\n"

    with open(memory_file, "a") as f:
        f.write(entry)


# ============================================================
# PARSE MEMORY UPDATES FROM ANALYSIS
# ============================================================

def find_todays_memory_updates():
    """
    Find all memory_updates.md files from today's analysis run.
    Returns a list of (story_slug, updates_file_path) tuples.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_parts = today.split("-")
    reports_dir = (PROJECT_ROOT / "reports" / date_parts[0] / date_parts[1] / date_parts[2])

    updates = []
    if not reports_dir.exists():
        return updates

    for story_dir in reports_dir.iterdir():
        if story_dir.is_dir():
            updates_file = story_dir / "memory_updates.md"
            structured_file = story_dir / "structured_data.json"

            if updates_file.exists():
                updates.append((story_dir.name, updates_file, structured_file))

    return updates


def load_structured_data(structured_file):
    """Load the structured analysis data for a story."""
    if not Path(structured_file).exists():
        return {}
    with open(structured_file) as f:
        return json.load(f)


def apply_memory_updates_from_json(story_slug, structured_data):
    """
    Apply memory updates extracted from the structured JSON analysis.
    This is more reliable than parsing the markdown memory_updates.md.
    """
    analysis = structured_data.get("analysis", {})
    memory_updates = analysis.get("memory_updates", {})

    if not memory_updates:
        print(f"    No memory updates for {story_slug}")
        return

    updates_applied = 0

    # 1. New insights -> master_memory.md
    for insight in memory_updates.get("new_insights", []):
        if insight and len(insight) > 10:
            add_master_memory(insight, story_slug)
            updates_applied += 1

    # 2. Thesis updates -> active_theses.md
    for thesis_update in memory_updates.get("thesis_updates", []):
        thesis_name = thesis_update.get("thesis", "")
        update_text = thesis_update.get("update", "")
        action = thesis_update.get("action", "strengthen")
        if thesis_name and update_text:
            update_thesis(thesis_name, update_text, action, story_slug)
            updates_applied += 1

    # 3. Pattern updates -> recurring_patterns.md
    for pattern_update in memory_updates.get("pattern_updates", []):
        pattern_name = pattern_update.get("pattern", "")
        observation = pattern_update.get("observation", "")
        if pattern_name and observation:
            update_pattern(pattern_name, observation, story_slug)
            updates_applied += 1

    # 4. New questions -> unresolved_questions.md
    for question in memory_updates.get("new_questions", []):
        if question and len(question) > 10:
            add_unresolved_question(question, story_slug)
            updates_applied += 1

    # 5. Entity updates -> world_model/
    for entity_update in memory_updates.get("entity_updates", []):
        entity_name = entity_update.get("entity", "")
        update_text = entity_update.get("update", "")
        if entity_name and update_text:
            # Guess entity type from key_entities in the analysis
            entity_type = "entity"
            for ke in analysis.get("key_entities", []):
                if ke.get("name", "").lower() == entity_name.lower():
                    entity_type = ke.get("type", "entity")
                    break
            update_entity_file(entity_name, entity_type, update_text, story_slug)
            updates_applied += 1

    # 6. Update worldview_evolution.md with meta-patterns
    meta_patterns = analysis.get("meta_patterns", [])
    if meta_patterns:
        evolution_file = PROJECT_ROOT / "memory" / "worldview_evolution.md"
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        entry = f"\n### {timestamp} [{story_slug}] — Meta-patterns observed:\n"
        for pattern in meta_patterns:
            entry += f"- {pattern}\n"
        with open(evolution_file, "a") as f:
            f.write(entry)
        updates_applied += 1

    print(f"    Applied {updates_applied} memory updates for {story_slug}")


def update_predictions_log(story_slug, structured_data):
    """
    Log future scenario predictions for tracking accuracy over time.
    """
    analysis = structured_data.get("analysis", {})
    scenarios = analysis.get("future_scenarios", {})
    title = structured_data.get("metadata", {}).get("title", "Unknown")

    if not scenarios:
        return

    predictions_file = PROJECT_ROOT / "memory" / "predictions.md"
    if not predictions_file.exists():
        # Create the file with header
        with open(predictions_file, "w") as f:
            f.write("""# Prediction Tracking Log

## Purpose
Track predictions made by the analysis system to measure accuracy over time.
Review this file periodically to assess calibration quality.

## Format
Each entry: story reference, prediction, confidence, review date, outcome

---

""")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    review_date = datetime.now(timezone.utc).replace(year=datetime.now().year + 1).strftime("%Y-%m-%d")

    entry = f"""
### {timestamp} — {title[:60]}
**Story:** {story_slug}

**Bull Scenario** ({scenarios.get('bull', {}).get('probability', '?')}):
{scenarios.get('bull', {}).get('description', '')[:200]}

**Base Scenario** ({scenarios.get('base', {}).get('probability', '?')}):
{scenarios.get('base', {}).get('description', '')[:200]}

**Bear Scenario** ({scenarios.get('bear', {}).get('probability', '?')}):
{scenarios.get('bear', {}).get('description', '')[:200]}

**Review by:** {review_date}
**Outcome:** *(To be filled in when resolution is clear)*

---
"""

    with open(predictions_file, "a") as f:
        f.write(entry)


# ============================================================
# RUN LOG
# ============================================================

def write_run_log(updates_applied, stories_processed):
    """Write a log of this memory update run."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f"memory_update_{today}.md"
    with open(log_file, "a") as f:
        f.write(f"""
## Run at {datetime.now(timezone.utc).strftime('%H:%M UTC')}
- Stories processed: {stories_processed}
- Memory updates applied: {updates_applied}
""")


# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "="*60)
    print("STEP 5: UPDATING MEMORY AND WORLD MODEL")
    print("="*60)

    # Find today's analyses
    updates_to_process = find_todays_memory_updates()
    print(f"\n  Found {len(updates_to_process)} stories with memory updates")

    if not updates_to_process:
        print("  No updates to process. Skipping.")
        return

    total_updates = 0

    for story_slug, updates_file, structured_file in updates_to_process:
        print(f"\n  Processing: {story_slug}")

        structured_data = load_structured_data(structured_file)

        if structured_data:
            # Apply updates from structured JSON (more reliable)
            apply_memory_updates_from_json(story_slug, structured_data)
            update_predictions_log(story_slug, structured_data)
            total_updates += 1
        else:
            print(f"    No structured data found, skipping")

    # Update worldview_evolution with a run summary
    evolution_file = PROJECT_ROOT / "memory" / "worldview_evolution.md"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    run_summary = f"\n## {today} — Daily Run\n"
    run_summary += f"- Stories analyzed: {len(updates_to_process)}\n"
    run_summary += f"- Memory files updated: {total_updates}\n"

    with open(evolution_file, "a") as f:
        f.write(run_summary)

    write_run_log(total_updates, len(updates_to_process))

    print(f"\n  Memory files updated: {total_updates}")
    print(f"  Files updated:")
    print(f"    - memory/master_memory.md")
    print(f"    - memory/active_theses.md")
    print(f"    - memory/recurring_patterns.md")
    print(f"    - memory/unresolved_questions.md")
    print(f"    - memory/worldview_evolution.md")
    print(f"    - memory/predictions.md")
    print(f"    - world_model/ (entity files)")

    print("\n" + "="*60)
    print("✓ STEP 5 COMPLETE: Memory updated")
    print("="*60)


if __name__ == "__main__":
    main()
