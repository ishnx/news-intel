#!/usr/bin/env python3
"""
run_pipeline.py - Main Intelligence Pipeline Orchestrator
==========================================================
Runs the complete intelligence pipeline in the correct sequence.
This is the single entry point for the automated GitHub Actions workflow.

PIPELINE STEPS:
  1. fetch_news.py    — Fetch articles from RSS feeds
  2. rank_news.py     — Score and rank by intelligence value
  3. analyze_story.py — Deep analysis with Claude API
  4. generate_report.py — Generate beautiful HTML reports
  5. update_memory.py — Update persistent memory and world model
  6. build_indexes.py — Build navigation index pages

RUN: python scripts/run_pipeline.py
     python scripts/run_pipeline.py --weekly  (for weekly digest mode)
     python scripts/run_pipeline.py --step fetch  (run single step)
"""

import subprocess
import sys
import os
import json
import yaml
import argparse
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def print_banner(title):
    print("\n" + "█"*60)
    print(f"  {title}")
    print("█"*60)


def print_separator(title=""):
    if title:
        print(f"\n{'─'*60}")
        print(f"  {title}")
        print(f"{'─'*60}")
    else:
        print(f"\n{'─'*60}")


def run_step(script_name, description, extra_args=None, allow_failure=False):
    """
    Run a pipeline step script and handle errors.
    Returns True on success, False on failure.
    """
    script_path = PROJECT_ROOT / "scripts" / script_name
    cmd = [sys.executable, str(script_path)]
    if extra_args:
        cmd.extend(extra_args)

    print_separator(f"Running: {description}")

    start_time = datetime.now(timezone.utc)
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

    if result.returncode == 0:
        print(f"\n  ✓ {description} completed ({elapsed:.1f}s)")
        return True
    else:
        print(f"\n  ✗ {description} FAILED (exit code {result.returncode}, {elapsed:.1f}s)")
        if not allow_failure:
            print(f"  Pipeline stopped. Check the output above for details.")
            sys.exit(result.returncode)
        return False


def check_api_key():
    """Verify the Anthropic API key is set."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("\n  ERROR: ANTHROPIC_API_KEY environment variable is not set!")
        print("\n  To fix this:")
        print("  - In GitHub Actions: Add ANTHROPIC_API_KEY to repository Secrets")
        print("    (Settings → Secrets and Variables → Actions → New Repository Secret)")
        print("  - For local testing: Run: export ANTHROPIC_API_KEY=your-key-here")
        sys.exit(1)
    print("  ✓ API key found")


def write_run_log(steps_run, start_time, success):
    """Write a run log to logs/ directory."""
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    status = "SUCCESS" if success else "FAILED"

    log_entry = {
        "run_at": start_time.isoformat(),
        "status": status,
        "elapsed_seconds": elapsed,
        "steps_run": steps_run,
        "date": today
    }

    log_file = log_dir / f"pipeline_{today}.json"
    # Append to existing log or create new
    existing_logs = []
    if log_file.exists():
        with open(log_file) as f:
            try:
                existing_logs = json.load(f)
            except Exception:
                existing_logs = []

    if isinstance(existing_logs, list):
        existing_logs.append(log_entry)
    else:
        existing_logs = [log_entry]

    with open(log_file, "w") as f:
        json.dump(existing_logs, f, indent=2)


def get_run_stats():
    """Get stats about today's pipeline run."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_parts = today.split("-")
    reports_dir = (PROJECT_ROOT / "reports" / date_parts[0] / date_parts[1] / date_parts[2])

    story_count = 0
    if reports_dir.exists():
        story_count = sum(1 for d in reports_dir.iterdir()
                         if d.is_dir() and (d / "structured_data.json").exists())

    return {"date": today, "stories": story_count}


def main():
    parser = argparse.ArgumentParser(description="World Intelligence Pipeline")
    parser.add_argument("--weekly", action="store_true", help="Run weekly digest mode")
    parser.add_argument("--step", help="Run only a specific step (fetch/rank/analyze/report/memory/index)")
    parser.add_argument("--dry-run", action="store_true", help="Skip API calls (for testing)")
    parser.add_argument("--topic", help="Ad-hoc topic/phrase to analyze directly (skips fetch + rank steps)")
    args = parser.parse_args()

    start_time = datetime.now(timezone.utc)
    steps_run = []

    print_banner(f"WORLD INTELLIGENCE PIPELINE — {start_time.strftime('%Y-%m-%d %H:%M UTC')}")

    # Validate environment
    print_separator("Pre-flight checks")
    check_api_key()

    # Load schedule config to show what we're about to do
    try:
        with open(PROJECT_ROOT / "config" / "schedules.yaml") as f:
            schedules = yaml.safe_load(f)
        stories_per_run = schedules.get("stories_per_run", 5)
        print(f"  Stories to analyze: {stories_per_run}")
        print(f"  Fetch window: {schedules.get('fetch_window_hours', 24)} hours")
    except Exception:
        print("  (Could not load schedules.yaml — using defaults)")

    # If --step is specified, run only that step
    if args.step:
        step_map = {
            "fetch": ("fetch_news.py", "Fetch News Feeds"),
            "rank": ("rank_news.py", "Rank News by Intelligence Value"),
            "analyze": ("analyze_story.py", "Deep Story Analysis"),
            "report": ("generate_report.py", "Generate HTML Reports"),
            "memory": ("update_memory.py", "Update Memory System"),
            "index": ("build_indexes.py", "Build Navigation Indexes"),
        }
        if args.step in step_map:
            script, description = step_map[args.step]
            run_step(script, description)
            print_separator()
            print(f"  Single step '{args.step}' complete.")
        else:
            print(f"  Unknown step: {args.step}")
            print(f"  Available steps: {', '.join(step_map.keys())}")
            sys.exit(1)
        return

    # Full pipeline run
    success = True

    if args.topic:
        # ── AD-HOC MODE: skip fetch+rank, go straight to analysis ──
        print_separator(f"AD-HOC MODE: analyzing '{args.topic}'")
        print("  Steps 1 and 2 (fetch/rank) are skipped for ad-hoc analysis.")

        if run_step("analyze_story.py", "Step 1/4 (ad-hoc): Deep Analysis",
                    extra_args=["--topic", args.topic]):
            steps_run.append("analyze")
        else:
            success = False
    else:
        # ── NORMAL MODE: full pipeline ──

        # Step 1: Fetch News
        if run_step("fetch_news.py", "Step 1/6: Fetch News Feeds"):
            steps_run.append("fetch")
        else:
            success = False

        # Step 2: Rank News
        if run_step("rank_news.py", "Step 2/6: Rank by Intelligence Value"):
            steps_run.append("rank")
        else:
            success = False

        # Step 3: Analyze Stories (most important step)
        if not args.dry_run:
            if run_step("analyze_story.py", "Step 3/6: Deep Analysis"):
                steps_run.append("analyze")
            else:
                success = False
        else:
            print_separator("Step 3/6: Deep Analysis (SKIPPED — dry run mode)")

    # Steps 4-6 run regardless of normal vs ad-hoc mode
    step_label = lambda n, total: f"Step {n}/{total}"
    total = 4 if args.topic else 6

    if run_step("generate_report.py", f"{step_label(2 if args.topic else 4, total)}: Generate HTML Reports"):
        steps_run.append("report")
    else:
        success = False

    if run_step("update_memory.py", f"{step_label(3 if args.topic else 5, total)}: Update Memory and World Model"):
        steps_run.append("memory")
    else:
        success = False

    if run_step("build_indexes.py", f"{step_label(4 if args.topic else 6, total)}: Build Navigation Indexes"):
        steps_run.append("index")
    else:
        success = False

    # Summary
    stats = get_run_stats()
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

    print_banner(f"PIPELINE {'COMPLETE ✓' if success else 'COMPLETED WITH ERRORS ✗'}")
    print(f"  Date: {stats['date']}")
    print(f"  Stories analyzed: {stats['stories']}")
    print(f"  Steps completed: {len(steps_run)}/6")
    print(f"  Total time: {elapsed:.0f}s ({elapsed/60:.1f} min)")

    if success:
        print(f"\n  All outputs committed to GitHub on next push.")
        print(f"  View on GitHub Pages: https://[your-username].github.io/[repo-name]/")
    else:
        print(f"\n  Some steps had errors. Check output above.")

    # Write run log
    write_run_log(steps_run, start_time, success)

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
