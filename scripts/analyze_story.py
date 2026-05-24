#!/usr/bin/env python3
"""
analyze_story.py - Deep Intelligence Analysis Engine
=====================================================
Takes top-ranked stories and produces deep structured analysis
using Claude. This is where raw news becomes intelligence.

RUN: python scripts/analyze_story.py
INPUT: staging/ranked/YYYY-MM-DD/top_stories.json
       + memory/ context files
       + config/analysis_prompt.md
OUTPUT: reports/YYYY/MM/DD/<story-slug>/structured_data.json
        reports/YYYY/MM/DD/<story-slug>/raw_analysis.md
        reports/YYYY/MM/DD/<story-slug>/summary.md
        reports/YYYY/MM/DD/<story-slug>/memory_updates.md
NEXT: scripts/generate_report.py
"""

import json
import os
import re
import sys
import yaml
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# CONFIGURATION
# ============================================================

def load_schedules():
    with open(PROJECT_ROOT / "config" / "schedules.yaml") as f:
        return yaml.safe_load(f)


def load_providers():
    """Load AI provider config from config/providers.yaml."""
    path = PROJECT_ROOT / "config" / "providers.yaml"
    with open(path) as f:
        return yaml.safe_load(f)


def load_analysis_prompt():
    """
    Load the analysis prompt from config/analysis_prompt.md.
    Extracts the SYSTEM PROMPT and USER PROMPT TEMPLATE sections.
    """
    path = PROJECT_ROOT / "config" / "analysis_prompt.md"
    with open(path) as f:
        content = f.read()

    # Extract system prompt (between ``` markers after "## SYSTEM PROMPT")
    system_match = re.search(r'## SYSTEM PROMPT\n```\n(.*?)```', content, re.DOTALL)
    system_prompt = system_match.group(1).strip() if system_match else ""

    # Extract user prompt template (between ```\n and the last ```)
    user_match = re.search(r'## USER PROMPT TEMPLATE\n```\n(.*?)```\n\n---', content, re.DOTALL)
    user_template = user_match.group(1).strip() if user_match else ""

    # If regex extraction failed, use full content as fallback
    if not system_prompt:
        system_prompt = "You are a world-class intelligence analyst. Analyze the provided news story and return structured JSON analysis."
    if not user_template:
        user_template = "Analyze this story:\n\nTitle: {story_title}\n\nContent: {story_content}\n\nReturn comprehensive JSON analysis."

    return system_prompt, user_template


# ============================================================
# MEMORY CONTEXT LOADING
# ============================================================

def load_memory_context(schedules):
    """
    Load relevant memory to send as context to Claude.
    This is what makes the system compound — each analysis is
    informed by everything that came before.
    """
    max_worldview = schedules.get("max_worldview_context_chars", 2000)
    max_memory = schedules.get("max_memory_context_chars", 4000)

    context = {}

    # 1. Current worldview
    worldview_path = PROJECT_ROOT / "config" / "worldview.md"
    if worldview_path.exists():
        with open(worldview_path) as f:
            worldview = f.read()
        context["worldview"] = worldview[:max_worldview]
    else:
        context["worldview"] = "No worldview context available yet."

    # 2. Active theses
    theses_path = PROJECT_ROOT / "memory" / "active_theses.md"
    if theses_path.exists():
        with open(theses_path) as f:
            theses = f.read()
        context["active_theses"] = theses[:1500]
    else:
        context["active_theses"] = "No active theses yet."

    # 3. Recurring patterns
    patterns_path = PROJECT_ROOT / "memory" / "recurring_patterns.md"
    if patterns_path.exists():
        with open(patterns_path) as f:
            patterns = f.read()
        context["recurring_patterns"] = patterns[:1000]
    else:
        context["recurring_patterns"] = "No recurring patterns identified yet."

    # 4. Unresolved questions
    questions_path = PROJECT_ROOT / "memory" / "unresolved_questions.md"
    if questions_path.exists():
        with open(questions_path) as f:
            questions = f.read()
        context["unresolved_questions"] = questions[:1000]
    else:
        context["unresolved_questions"] = "No open questions yet."

    # 5. Recent report titles (for connection-making)
    recent_reports = load_recent_report_summaries(schedules)
    context["recent_summaries"] = recent_reports

    return context


def load_recent_report_summaries(schedules, max_reports=10):
    """
    Load brief summaries of recent reports for context.
    Helps Claude make connections between current and past stories.
    """
    summaries = []
    reports_dir = PROJECT_ROOT / "reports"

    if not reports_dir.exists():
        return "No previous reports yet."

    # Walk the reports directory and find summary.md files
    all_summaries = []
    for summary_file in reports_dir.rglob("summary.md"):
        try:
            with open(summary_file) as f:
                content = f.read()
            # Get the modification time for sorting
            mtime = summary_file.stat().st_mtime
            all_summaries.append((mtime, content[:500], str(summary_file)))
        except Exception:
            pass

    # Sort by modification time (most recent first)
    all_summaries.sort(key=lambda x: x[0], reverse=True)

    # Return just the text of the most recent N summaries
    for _, summary_text, path in all_summaries[:max_reports]:
        summaries.append(summary_text)

    if not summaries:
        return "No previous reports yet."

    return "\n\n---\n\n".join(summaries)


# ============================================================
# STORY SLUG GENERATION
# ============================================================

def make_slug(title, date_str):
    """
    Convert a story title to a URL-safe slug.
    Example: "AI Chip Exports Restricted" -> "ai-chip-exports-restricted"
    """
    # Lowercase and remove non-alphanumeric chars
    slug = re.sub(r'[^a-z0-9\s-]', '', title.lower())
    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug.strip())
    # Truncate to reasonable length
    slug = slug[:60].rstrip('-')
    return slug


# ============================================================
# CLAUDE API CALL
# ============================================================

def safe_fill_template(template, **kwargs):
    """
    Fill {variable} placeholders in a template that also contains JSON or code
    blocks with curly braces (which would normally crash Python's str.format).

    How it works:
    1. Replace each {our_variable} with a unique null-byte token
    2. Escape all remaining { and } so str.format won't choke on them
    3. Restore our actual variable values from the tokens

    This means the template file (config/analysis_prompt.md) can use the natural
    {variable_name} syntax for placeholders alongside JSON schema examples —
    no special escaping needed by the template author.
    """
    result = template
    token_map = {}

    for key, value in kwargs.items():
        placeholder = '{' + key + '}'
        if placeholder in result:
            # Unique token that cannot appear in real content
            token = f'\x00TMPL_{key.upper()}_END\x00'
            result = result.replace(placeholder, token)
            token_map[token] = str(value)

    # Now all remaining { and } are literal (JSON, code examples, etc.)
    # Escape them so they pass through format() unchanged
    result = result.replace('{', '{{').replace('}', '}}')

    # Restore our substitutions with actual values
    for token, value in token_map.items():
        result = result.replace(token, value)

    return result


def _build_user_prompt(story, memory_context, user_template):
    """Build the user prompt from template — shared across all providers."""
    return safe_fill_template(
        user_template,
        current_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        worldview_context=memory_context.get("worldview", ""),
        active_theses=memory_context.get("active_theses", ""),
        recurring_patterns=memory_context.get("recurring_patterns", ""),
        unresolved_questions=memory_context.get("unresolved_questions", ""),
        recent_report_summaries=memory_context.get("recent_summaries", ""),
        story_title=story.get("title", ""),
        story_source=story.get("source_name", ""),
        story_date=story.get("published_at", "")[:10],
        story_category=story.get("category", ""),
        story_url=story.get("url", ""),
        story_content=story.get("summary", "")
    )


def _call_anthropic(system_prompt, user_prompt, model, max_tokens):
    """Call Anthropic Claude API."""
    import anthropic as _anthropic
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        print("ERROR: ANTHROPIC_API_KEY not set. Add it to GitHub Secrets.")
        sys.exit(1)
    client = _anthropic.Anthropic(api_key=key)
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}]
    )
    text = message.content[0].text
    print(f"    Input tokens: {message.usage.input_tokens} | Output tokens: {message.usage.output_tokens}")
    return text, message.usage


def _call_openai(system_prompt, user_prompt, model, max_tokens):
    """Call OpenAI API."""
    import openai as _openai
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        print("ERROR: OPENAI_API_KEY not set. Add it to GitHub Secrets.")
        sys.exit(1)
    client = _openai.OpenAI(api_key=key)
    response = client.chat.completions.create(
        model=model,
        max_tokens=max_tokens,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    text = response.choices[0].message.content
    usage = response.usage
    print(f"    Input tokens: {usage.prompt_tokens} | Output tokens: {usage.completion_tokens}")
    return text, usage


def _call_google(system_prompt, user_prompt, model, max_tokens):
    """Call Google Gemini API."""
    import google.generativeai as _genai
    key = os.environ.get("GOOGLE_API_KEY")
    if not key:
        print("ERROR: GOOGLE_API_KEY not set. Add it to GitHub Secrets.")
        sys.exit(1)
    _genai.configure(api_key=key)
    model_obj = _genai.GenerativeModel(
        model,
        system_instruction=system_prompt
    )
    response = model_obj.generate_content(
        user_prompt,
        generation_config={"max_output_tokens": max_tokens}
    )
    text = response.text
    print(f"    Response length: {len(text)} chars")
    return text, None


def call_ai_provider(story, memory_context, system_prompt, user_template, max_tokens):
    """
    Send the story to the configured AI provider for deep analysis.
    Provider and model are read from config/providers.yaml.
    Returns (raw_json_string, usage_object).
    """
    providers_config = load_providers()
    provider = providers_config.get("active_provider", "anthropic")
    model = providers_config.get(provider, {}).get("model", "")

    user_prompt = _build_user_prompt(story, memory_context, user_template)

    print(f"\n    Calling {provider.upper()} API (model: {model})...")
    print(f"    Story: {story.get('title', '')[:60]}...")

    if provider == "anthropic":
        return _call_anthropic(system_prompt, user_prompt, model, max_tokens)
    elif provider == "openai":
        return _call_openai(system_prompt, user_prompt, model, max_tokens)
    elif provider == "google":
        return _call_google(system_prompt, user_prompt, model, max_tokens)
    else:
        print(f"ERROR: Unknown provider '{provider}'. Set active_provider in config/providers.yaml.")
        sys.exit(1)


# Keep old name as alias so any external callers don't break
analyze_with_claude = call_ai_provider


# ============================================================
# RESPONSE PARSING
# ============================================================

def parse_analysis_response(response_text, story):
    """
    Parse Claude's JSON response into a structured dict.
    Handles common issues like markdown code blocks around the JSON.
    """
    # Claude often wraps JSON in ```json ... ``` code blocks
    json_text = response_text.strip()

    # Strip markdown code fence if present
    if json_text.startswith("```"):
        lines = json_text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        json_text = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        json_text = json_text.strip()

    try:
        analysis = json.loads(json_text)
        return analysis, None
    except json.JSONDecodeError as e:
        # If JSON parsing fails, try to extract just the JSON object
        # by finding the first { and last }
        start = json_text.find('{')
        end = json_text.rfind('}')

        if start != -1 and end != -1:
            try:
                analysis = json.loads(json_text[start:end+1])
                return analysis, f"JSON extraction required (offset {start}-{end})"
            except json.JSONDecodeError:
                pass

        # Complete failure — return a minimal structure with the raw text
        print(f"    WARNING: Could not parse JSON response. Saving raw text.")
        return {
            "executive_summary": "Analysis failed to parse. See raw_analysis.md for full response.",
            "why_this_matters": story.get("summary", ""),
            "parse_error": str(e),
            "raw_response": response_text[:1000]
        }, f"JSON parse failed: {e}"


# ============================================================
# OUTPUT PERSISTENCE
# ============================================================

def save_analysis(story, analysis, raw_response, usage, output_dir):
    """
    Save all analysis artifacts to the report directory.

    Creates:
    - structured_data.json: The full structured analysis
    - raw_analysis.md: Human-readable version of the analysis
    - summary.md: Brief summary for quick reference and memory context
    - memory_updates.md: Pending memory updates for update_memory.py
    - connections.md: Story connections to world model
    - followup_questions.md: Questions raised by this analysis
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. structured_data.json — the complete machine-readable record
    structured_data = {
        "metadata": {
            "story_id": output_dir.name,
            "title": story.get("title", ""),
            "source_name": story.get("source_name", ""),
            "source_url": story.get("url", ""),
            "published_at": story.get("published_at", ""),
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "intelligence_score": story.get("intelligence_score", 0),
            "category": story.get("category", ""),
            "matched_topics": story.get("score_breakdown", {}).get("matched_topics", []),
            "api_usage": {
                "input_tokens": getattr(usage, 'input_tokens', 0) if usage else 0,
                "output_tokens": getattr(usage, 'output_tokens', 0) if usage else 0
            } if usage else {}
        },
        "analysis": analysis
    }

    with open(output_dir / "structured_data.json", "w") as f:
        json.dump(structured_data, f, indent=2, ensure_ascii=False)

    # 2. raw_analysis.md — the full raw Claude response
    raw_md = f"""# Raw Analysis: {story.get('title', '')}
**Analyzed:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
**Source:** {story.get('source_name', '')}
**URL:** {story.get('url', '')}

---

## Raw Claude Response

```json
{raw_response}
```
"""
    with open(output_dir / "raw_analysis.md", "w") as f:
        f.write(raw_md)

    # 3. summary.md — brief summary for future context
    exec_summary = analysis.get("executive_summary", "No summary available.")
    why_matters = analysis.get("why_this_matters", "")
    tags = analysis.get("intelligence_tags", [])

    summary_md = f"""# {story.get('title', '')}
**Date:** {story.get('published_at', '')[:10]}
**Source:** {story.get('source_name', '')}
**Category:** {story.get('category', '')}
**Score:** {story.get('intelligence_score', 0):.1f}
**Tags:** {', '.join(tags)}

## Executive Summary
{exec_summary}

## Why This Matters
{why_matters[:500] if isinstance(why_matters, str) else ''}

---
*Full analysis: [structured_data.json](structured_data.json)*
"""
    with open(output_dir / "summary.md", "w") as f:
        f.write(summary_md)

    # 4. memory_updates.md — instructions for update_memory.py
    memory_updates = analysis.get("memory_updates", {})
    updates_md = f"""# Memory Updates: {story.get('title', '')}
**Source Story:** {output_dir.name}
**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d')}

## New Insights
{chr(10).join('- ' + i for i in memory_updates.get('new_insights', []))}

## Thesis Updates
"""
    for tu in memory_updates.get("thesis_updates", []):
        updates_md += f"""
### {tu.get('thesis', 'Unknown Thesis')}
- **Action:** {tu.get('action', 'update')}
- **Update:** {tu.get('update', '')}
"""

    updates_md += "\n## Pattern Updates\n"
    for pu in memory_updates.get("pattern_updates", []):
        updates_md += f"- **{pu.get('pattern', '')}**: {pu.get('observation', '')}\n"

    updates_md += "\n## New Unresolved Questions\n"
    for q in memory_updates.get("new_questions", []):
        updates_md += f"- {q}\n"

    updates_md += "\n## Entity Updates\n"
    for eu in memory_updates.get("entity_updates", []):
        updates_md += f"- **{eu.get('entity', '')}**: {eu.get('update', '')}\n"

    with open(output_dir / "memory_updates.md", "w") as f:
        f.write(updates_md)

    # 5. connections.md — world model connections
    connections = analysis.get("connection_to_world_model", "")
    related_themes = analysis.get("related_themes", [])
    connections_md = f"""# Connections: {story.get('title', '')}

## Connection to World Model
{connections}

## Related Themes
{chr(10).join('- ' + t for t in related_themes)}

## Key Entities
"""
    for entity in analysis.get("key_entities", []):
        connections_md += f"- **{entity.get('name', '')}** ({entity.get('type', '')}): {entity.get('significance', '')}\n"

    with open(output_dir / "connections.md", "w") as f:
        f.write(connections_md)

    # 6. followup_questions.md
    questions = analysis.get("followup_questions", [])
    questions_md = f"""# Follow-up Questions: {story.get('title', '')}

*Questions raised by this analysis for future investigation.*

"""
    for i, q in enumerate(questions, 1):
        questions_md += f"{i}. {q}\n"

    with open(output_dir / "followup_questions.md", "w") as f:
        f.write(questions_md)

    print(f"    Saved analysis to {output_dir.relative_to(PROJECT_ROOT)}/")
    return structured_data


# ============================================================
# MAIN
# ============================================================

def make_adhoc_story(topic):
    """Create a synthetic story object from a user-supplied topic/phrase."""
    return {
        "title": topic,
        "source_name": "Ad-hoc Analysis",
        "published_at": datetime.now(timezone.utc).isoformat(),
        "category": "general",
        "url": "",
        "summary": (
            f"This is an ad-hoc deep-dive requested for the following topic: {topic}. "
            "Apply your full analytical framework to this subject as if it were a breaking news story. "
            "Draw on your accumulated world knowledge, historical patterns, geopolitical context, "
            "and India-specific lens to produce a thorough intelligence analysis."
        ),
        "intelligence_score": 100.0,
        "rank": 1,
    }


def main():
    parser = argparse.ArgumentParser(description="Intelligence Analysis Engine")
    parser.add_argument(
        "--topic",
        help="Ad-hoc topic or phrase to analyze directly (skips fetch/rank steps)",
        default=None
    )
    args = parser.parse_args()

    print("\n" + "="*60)
    if args.topic:
        print("STEP 3: AD-HOC INTELLIGENCE ANALYSIS")
        print(f"Topic: {args.topic}")
    else:
        print("STEP 3: DEEP INTELLIGENCE ANALYSIS")
    print("="*60)

    # Load configuration
    schedules = load_schedules()
    providers_config = load_providers()
    max_tokens = schedules.get("max_tokens_per_analysis", 6000)
    system_prompt, user_template = load_analysis_prompt()

    active_provider = providers_config.get("active_provider", "anthropic")
    active_model = providers_config.get(active_provider, {}).get("model", "?")
    print(f"\n  Provider: {active_provider} | Model: {active_model}")
    print(f"  Max tokens per analysis: {max_tokens}")

    # Load memory context (what the system knows so far)
    print("\n  Loading memory context...")
    memory_context = load_memory_context(schedules)
    print(f"  Worldview context: {len(memory_context.get('worldview', ''))} chars")
    print(f"  Theses context: {len(memory_context.get('active_theses', ''))} chars")
    print(f"  Patterns context: {len(memory_context.get('recurring_patterns', ''))} chars")

    # Determine stories to analyze
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if args.topic:
        # Ad-hoc mode: create a synthetic story from the topic
        stories = [make_adhoc_story(args.topic)]
        print(f"\n  Ad-hoc mode: analyzing '{args.topic}'")
    else:
        # Normal mode: load top stories from ranking step
        top_stories_path = PROJECT_ROOT / "staging" / "ranked" / today / "top_stories.json"
        if not top_stories_path.exists():
            print(f"\n  ERROR: No ranked stories found at {top_stories_path}")
            print("  Run rank_news.py first!")
            sys.exit(1)
        with open(top_stories_path) as f:
            data = json.load(f)
        stories = data.get("stories", [])

    print(f"\n  Stories to analyze: {len(stories)}")

    if not stories:
        print("  No stories to analyze. Exiting.")
        return

    # Analyze each story
    analyzed_count = 0
    failed_count = 0

    for i, story in enumerate(stories, 1):
        title = story.get("title", "Unknown")
        print(f"\n  [{i}/{len(stories)}] Analyzing: {title[:60]}...")

        # Create output directory
        date_parts = today.split("-")
        slug = make_slug(title, today)
        output_dir = (PROJECT_ROOT / "reports" / date_parts[0] / date_parts[1]
                     / date_parts[2] / slug)

        # Skip if already analyzed (allows re-running)
        if (output_dir / "structured_data.json").exists():
            print(f"    Already analyzed — skipping (delete dir to re-analyze)")
            analyzed_count += 1
            continue

        try:
            # Call AI provider (configured in config/providers.yaml)
            raw_response, usage = call_ai_provider(
                story=story,
                memory_context=memory_context,
                system_prompt=system_prompt,
                user_template=user_template,
                max_tokens=max_tokens
            )

            # Parse the response
            analysis, parse_warning = parse_analysis_response(raw_response, story)

            if parse_warning:
                print(f"    WARNING: {parse_warning}")

            # Save all outputs
            save_analysis(story, analysis, raw_response, usage, output_dir)
            analyzed_count += 1

            # Brief pause between API calls to avoid rate limiting
            if i < len(stories):
                print(f"    Waiting 3 seconds before next analysis...")
                time.sleep(3)

        except Exception as e:
            print(f"    ERROR analyzing story: {type(e).__name__}: {e}")
            print(f"    Continuing with remaining stories...")
            failed_count += 1

            # Save a partial record so we know this story was attempted
            output_dir.mkdir(parents=True, exist_ok=True)
            with open(output_dir / "error.json", "w") as f:
                json.dump({
                    "error": str(e),
                    "story": story,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)

    print(f"\n  Analyzed: {analyzed_count} | Failed: {failed_count}")

    print("\n" + "="*60)
    print(f"✓ STEP 3 COMPLETE: {analyzed_count} stories analyzed")
    print("="*60)


if __name__ == "__main__":
    main()
