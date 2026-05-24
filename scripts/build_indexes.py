#!/usr/bin/env python3
"""
build_indexes.py - Index and Navigation Builder
================================================
Builds the main index pages for GitHub Pages navigation.
Creates the site's front page, daily digests, and archive.

RUN: python scripts/build_indexes.py
INPUT: reports/ directory structure
OUTPUT: index.html (root)
        reports/index.html
        intelligence/daily/index.html
        intelligence/weekly/index.html
NEXT: (end of pipeline — commit and push)
"""

import json
import os
import sys
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Site base URL — set by GitHub Actions CI step; defaults to "/" for local.
SITE_BASE = os.environ.get("SITE_BASE_URL", "/")


# ============================================================
# DATA COLLECTION
# ============================================================

def load_all_reports(max_reports=200):
    """
    Scan the reports/ directory and load metadata from all structured_data.json files.
    Returns a list of report dicts sorted by date (newest first).
    """
    reports = []
    reports_dir = PROJECT_ROOT / "reports"

    if not reports_dir.exists():
        return reports

    for data_file in reports_dir.rglob("structured_data.json"):
        try:
            with open(data_file) as f:
                data = json.load(f)

            meta = data.get("metadata", {})
            analysis = data.get("analysis", {})

            # Reconstruct the URL path for linking
            rel_path = data_file.parent.relative_to(PROJECT_ROOT)
            url_path = str(rel_path).replace("\\", "/")

            report = {
                "slug": data_file.parent.name,
                "title": meta.get("title", "Untitled"),
                "date": meta.get("published_at", meta.get("analyzed_at", ""))[:10],
                "analyzed_at": meta.get("analyzed_at", "")[:19],
                "source": meta.get("source_name", "Unknown"),
                "category": meta.get("category", "general"),
                "score": meta.get("intelligence_score", 0),
                "tags": analysis.get("intelligence_tags", []),
                "topics": meta.get("matched_topics", []),
                "executive_summary": analysis.get("executive_summary", ""),
                "why_matters": analysis.get("why_this_matters", "")[:200] if isinstance(analysis.get("why_this_matters"), str) else "",
                "url": f"{url_path}/index.html",  # Relative — works with <base href>
                "path": str(data_file.parent.relative_to(PROJECT_ROOT))
            }
            reports.append(report)

        except Exception as e:
            pass  # Skip malformed files silently

    # Sort by analyzed_at (newest first)
    reports.sort(key=lambda r: r.get("analyzed_at", ""), reverse=True)
    return reports[:max_reports]


def load_memory_stats():
    """Load statistics from memory files for dashboard display."""
    stats = {
        "total_insights": 0,
        "active_theses": 0,
        "recurring_patterns": 0,
        "unresolved_questions": 0
    }

    memory_dir = PROJECT_ROOT / "memory"

    # Count bullet points in master_memory.md
    memory_file = memory_dir / "master_memory.md"
    if memory_file.exists():
        with open(memory_file) as f:
            content = f.read()
        stats["total_insights"] = content.count("\n- **")

    # Count theses sections in active_theses.md
    theses_file = memory_dir / "active_theses.md"
    if theses_file.exists():
        with open(theses_file) as f:
            content = f.read()
        stats["active_theses"] = len(re.findall(r'^## .+', content, re.MULTILINE))

    # Count patterns
    patterns_file = memory_dir / "recurring_patterns.md"
    if patterns_file.exists():
        with open(patterns_file) as f:
            content = f.read()
        stats["recurring_patterns"] = len(re.findall(r'^## .+', content, re.MULTILINE))

    # Count questions
    questions_file = memory_dir / "unresolved_questions.md"
    if questions_file.exists():
        with open(questions_file) as f:
            content = f.read()
        stats["unresolved_questions"] = content.count("\n- **")

    return stats


# ============================================================
# REPORT CARD HTML
# ============================================================

def make_report_card(report, compact=False):
    """
    Generate an HTML card for a single report.
    The data-category attribute is built directly here — never via post-processing
    string replacement, which was fragile and could corrupt HTML.
    """
    tags_html = "".join(f'<span class="tag">{t}</span>' for t in report.get("tags", [])[:4])
    score = report.get("score", 0)
    score_color = "#4ade80" if score >= 70 else "#fbbf24" if score >= 50 else "#8892b0"
    category = report.get("category", "general")

    category_icons = {
        "technology": "⚡", "ai": "🤖", "geopolitics": "🌍",
        "macro": "📊", "india": "🇮🇳", "energy": "⚡",
        "finance": "💰", "science": "🔬", "manual": "📌"
    }
    icon = category_icons.get(category, "📰")
    url = report.get("url", "#")

    if compact:
        return f"""<div class="report-card compact" data-category="{category}" onclick="window.location='{url}'">
  <div class="card-header">
    <span class="card-icon">{icon}</span>
    <span class="card-date">{report.get('date', '')}</span>
    <span class="card-score" style="color:{score_color}">{score:.0f}</span>
  </div>
  <h3 class="card-title">{report.get('title', '')}</h3>
  <div class="card-source">{report.get('source', '')}</div>
</div>"""

    summary = report.get("executive_summary", "")[:200]
    if summary and len(report.get("executive_summary", "")) > 200:
        summary += "..."

    return f"""<div class="report-card" data-category="{category}" onclick="window.location='{url}'">
  <div class="card-header">
    <div class="card-meta">
      <span class="card-icon">{icon}</span>
      <span class="card-category">{category}</span>
      <span class="card-date">{report.get('date', '')}</span>
    </div>
    <span class="card-score" style="color:{score_color}" title="Intelligence Score">{score:.0f}</span>
  </div>
  <h3 class="card-title">{report.get('title', '')}</h3>
  <p class="card-summary">{summary}</p>
  <div class="card-footer">
    <span class="card-source">{report.get('source', '')}</span>
    <div class="card-tags">{tags_html}</div>
    <a href="{url}" class="card-link">Read Analysis →</a>
  </div>
</div>"""


# ============================================================
# MAIN INDEX PAGE (GitHub Pages root)
# ============================================================

def build_main_index(reports, stats):
    """Build the main index.html landing page."""

    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Recent reports (last 7 days)
    recent_reports = [r for r in reports if r.get("date", "") >= (
        datetime.now(timezone.utc) - timedelta(days=7)
    ).strftime("%Y-%m-%d")]

    # Today's reports
    todays_reports = [r for r in reports if r.get("date", "") == today_str]

    # Top reports by score
    top_reports = sorted(reports[:30], key=lambda r: r.get("score", 0), reverse=True)[:5]

    recent_cards = "\n".join(make_report_card(r) for r in recent_reports[:6])
    top_cards = "\n".join(make_report_card(r, compact=True) for r in top_reports)

    if not recent_cards:
        recent_cards = '<div class="empty-state"><p>No reports yet. The system will populate this after the first automated run.</p><p>If you just set up the system, trigger a manual run via <strong>GitHub Actions → intelligence.yml → Run workflow</strong>.</p></div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>World Intelligence System</title>
  <base href="{SITE_BASE}">
  <style>
    :root {{
      --bg: #08090e; --surface: #0f1117; --surface2: #13141c;
      --border: #1e2036; --accent: #6366f1; --accent2: #818cf8;
      --text: #e4e6f0; --text2: #8892b0; --text3: #4b5280;
      --bull: #4ade80; --bear: #f87171; --base: #fbbf24;
      --radius: 12px; --radius-sm: 6px;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; }}
    a {{ color: var(--accent2); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}

    /* HEADER */
    .site-header {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 0 24px; position: sticky; top: 0; z-index: 100; }}
    .header-inner {{ max-width: 1200px; margin: 0 auto; display: flex; align-items: center; justify-content: space-between; height: 60px; }}
    .logo {{ font-size: 18px; font-weight: 700; color: var(--text); letter-spacing: -0.5px; }}
    .logo span {{ color: var(--accent); }}
    .header-nav {{ display: flex; gap: 24px; }}
    .header-nav a {{ color: var(--text2); font-size: 14px; transition: color 0.2s; }}
    .header-nav a:hover {{ color: var(--text); text-decoration: none; }}
    .last-updated {{ font-size: 12px; color: var(--text3); }}

    /* HERO */
    .hero {{ max-width: 1200px; margin: 0 auto; padding: 48px 24px 32px; }}
    .hero-title {{ font-size: 36px; font-weight: 700; letter-spacing: -1px; margin-bottom: 8px; }}
    .hero-title span {{ color: var(--accent); }}
    .hero-subtitle {{ color: var(--text2); font-size: 16px; max-width: 600px; margin-bottom: 32px; }}

    /* STATS BAR */
    .stats-bar {{ display: flex; gap: 16px; margin-bottom: 48px; flex-wrap: wrap; }}
    .stat-chip {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 20px; }}
    .stat-value {{ font-size: 28px; font-weight: 700; color: var(--accent2); }}
    .stat-label {{ font-size: 12px; color: var(--text2); margin-top: 2px; }}

    /* SECTIONS */
    .section {{ max-width: 1200px; margin: 0 auto; padding: 0 24px 48px; }}
    .section-header {{ display: flex; align-items: baseline; gap: 12px; margin-bottom: 24px; }}
    .section-title {{ font-size: 20px; font-weight: 600; }}
    .section-link {{ font-size: 13px; color: var(--accent2); }}

    /* GRID */
    .reports-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }}
    .reports-grid.compact {{ grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 12px; }}

    /* REPORT CARD */
    .report-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; cursor: pointer; transition: border-color 0.2s, transform 0.2s; }}
    .report-card:hover {{ border-color: var(--accent); transform: translateY(-2px); }}
    .report-card.compact {{ padding: 14px; }}
    .card-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }}
    .card-meta {{ display: flex; align-items: center; gap: 8px; }}
    .card-icon {{ font-size: 16px; }}
    .card-category {{ font-size: 11px; background: var(--surface2); border: 1px solid var(--border); border-radius: 4px; padding: 2px 7px; color: var(--text2); text-transform: uppercase; letter-spacing: 0.5px; }}
    .card-date {{ font-size: 12px; color: var(--text3); }}
    .card-score {{ font-size: 16px; font-weight: 700; }}
    .card-title {{ font-size: 15px; font-weight: 600; line-height: 1.4; margin-bottom: 10px; color: var(--text); }}
    .report-card.compact .card-title {{ font-size: 13px; margin-bottom: 6px; }}
    .card-summary {{ font-size: 13px; color: var(--text2); line-height: 1.6; margin-bottom: 14px; }}
    .card-footer {{ display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 8px; }}
    .card-source {{ font-size: 11px; color: var(--text3); }}
    .card-tags {{ display: flex; gap: 6px; flex-wrap: wrap; }}
    .tag {{ font-size: 10px; background: var(--surface2); border: 1px solid var(--border); border-radius: 3px; padding: 2px 6px; color: var(--text2); }}
    .card-link {{ font-size: 12px; color: var(--accent2); font-weight: 500; }}
    .empty-state {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 40px; text-align: center; color: var(--text2); }}
    .empty-state p {{ margin-bottom: 12px; }}

    /* MEMORY PANEL */
    .memory-panel {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; margin-bottom: 48px; }}
    .memory-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; margin-top: 16px; }}
    .memory-stat {{ border-left: 3px solid var(--accent); padding-left: 12px; }}
    .memory-stat-value {{ font-size: 24px; font-weight: 700; color: var(--text); }}
    .memory-stat-label {{ font-size: 12px; color: var(--text2); }}

    /* FOOTER */
    footer {{ border-top: 1px solid var(--border); padding: 24px; text-align: center; color: var(--text3); font-size: 12px; }}

    @media (max-width: 600px) {{
      .hero-title {{ font-size: 24px; }}
      .reports-grid {{ grid-template-columns: 1fr; }}
      .header-nav {{ display: none; }}
    }}
  </style>
</head>
<body>
  <header class="site-header">
    <div class="header-inner">
      <div class="logo">World<span>Intel</span></div>
      <nav class="header-nav">
        <a href="reports/index.html">Archive</a>
        <a href="intelligence/daily/index.html">Daily</a>
        <a href="intelligence/weekly/index.html">Weekly</a>
        <a href="memory/master_memory.md">Memory</a>
        <a href="config/worldview.md">Worldview</a>
        <a href="config.html">⚙ Config</a>
        <a href="guide.html">Guide</a>
        <a href="how_this_works.html">How It Works</a>
      </nav>
      <div class="last-updated">Updated: {today}</div>
    </div>
  </header>

  <div class="hero">
    <h1 class="hero-title">World <span>Intelligence</span> System</h1>
    <p class="hero-subtitle">Autonomous deep analysis of global events — technology, geopolitics, economics, India. Compounds knowledge over time.</p>

    <div class="stats-bar">
      <div class="stat-chip">
        <div class="stat-value">{len(reports)}</div>
        <div class="stat-label">Total Reports</div>
      </div>
      <div class="stat-chip">
        <div class="stat-value">{len(todays_reports)}</div>
        <div class="stat-label">Today</div>
      </div>
      <div class="stat-chip">
        <div class="stat-value">{len(recent_reports)}</div>
        <div class="stat-label">This Week</div>
      </div>
      <div class="stat-chip">
        <div class="stat-value">{stats.get('active_theses', 0)}</div>
        <div class="stat-label">Active Theses</div>
      </div>
      <div class="stat-chip">
        <div class="stat-value">{stats.get('total_insights', 0)}</div>
        <div class="stat-label">Accumulated Insights</div>
      </div>
    </div>
  </div>

  <div class="section">
    <div class="memory-panel">
      <div class="section-header">
        <h2 class="section-title">Knowledge Base</h2>
        <a href="memory/master_memory.md" class="section-link">View full memory →</a>
      </div>
      <div class="memory-grid">
        <div class="memory-stat">
          <div class="memory-stat-value">{stats.get('total_insights', 0)}</div>
          <div class="memory-stat-label">Stored Insights</div>
        </div>
        <div class="memory-stat">
          <div class="memory-stat-value">{stats.get('active_theses', 0)}</div>
          <div class="memory-stat-label">Active Theses</div>
        </div>
        <div class="memory-stat">
          <div class="memory-stat-value">{stats.get('recurring_patterns', 0)}</div>
          <div class="memory-stat-label">Recurring Patterns</div>
        </div>
        <div class="memory-stat">
          <div class="memory-stat-value">{stats.get('unresolved_questions', 0)}</div>
          <div class="memory-stat-label">Open Questions</div>
        </div>
      </div>
    </div>
  </div>

  <div class="section">
    <div class="section-header">
      <h2 class="section-title">Recent Intelligence</h2>
      <a href="reports/index.html" class="section-link">Full archive →</a>
    </div>
    <div class="reports-grid">
      {recent_cards}
    </div>
  </div>

  <div class="section">
    <div class="section-header">
      <h2 class="section-title">Highest Signal Reports</h2>
      <a href="reports/index.html" class="section-link">All reports →</a>
    </div>
    <div class="reports-grid compact">
      {top_cards}
    </div>
  </div>

  <footer>
    <p>Autonomous Intelligence System — Powered by Claude API + GitHub Actions</p>
    <p>All analysis is AI-generated. Verify important claims independently.</p>
  </footer>
</body>
</html>"""

    output_path = PROJECT_ROOT / "index.html"
    with open(output_path, "w") as f:
        f.write(html)
    print(f"  Built: index.html")


# ============================================================
# REPORTS ARCHIVE PAGE
# ============================================================

def build_reports_archive(reports):
    """Build the full reports archive page with filtering."""
    cards_html = "\n".join(make_report_card(r) for r in reports)

    # Get all unique categories and tags
    categories = sorted(set(r.get("category", "general") for r in reports))
    all_tags = set()
    for r in reports:
        all_tags.update(r.get("tags", []))
    top_tags = sorted(all_tags)[:20]

    category_buttons = "".join(
        f'<button class="filter-btn" onclick="filterByCategory(\'{c}\')">{c}</button>'
        for c in categories
    )

    if not cards_html:
        cards_html = '<div class="empty-state"><p>No reports yet. The pipeline will populate this automatically.</p></div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Intelligence Archive — World Intel</title>
  <base href="{SITE_BASE}">
  <style>
    :root {{ --bg: #08090e; --surface: #0f1117; --border: #1e2036; --accent: #6366f1; --accent2: #818cf8; --text: #e4e6f0; --text2: #8892b0; --text3: #4b5280; --radius: 12px; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; }}
    a {{ color: var(--accent2); text-decoration: none; }}
    .header {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 16px 24px; display: flex; align-items: center; gap: 24px; }}
    .back-link {{ color: var(--text2); font-size: 14px; }}
    h1 {{ font-size: 20px; font-weight: 700; }}
    .content {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}
    .filters {{ margin-bottom: 24px; display: flex; gap: 8px; flex-wrap: wrap; }}
    .filter-btn {{ background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 6px 14px; color: var(--text2); font-size: 13px; cursor: pointer; transition: all 0.2s; }}
    .filter-btn:hover, .filter-btn.active {{ background: var(--accent); border-color: var(--accent); color: white; }}
    .reports-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }}
    .report-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; cursor: pointer; transition: border-color 0.2s; }}
    .report-card:hover {{ border-color: var(--accent); }}
    .card-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }}
    .card-meta {{ display: flex; align-items: center; gap: 8px; }}
    .card-category {{ font-size: 11px; background: #13141c; border: 1px solid var(--border); border-radius: 4px; padding: 2px 7px; color: var(--text2); text-transform: uppercase; }}
    .card-date {{ font-size: 12px; color: var(--text3); }}
    .card-score {{ font-size: 16px; font-weight: 700; color: #4ade80; }}
    .card-title {{ font-size: 15px; font-weight: 600; line-height: 1.4; margin-bottom: 10px; }}
    .card-summary {{ font-size: 13px; color: var(--text2); margin-bottom: 14px; }}
    .card-footer {{ display: flex; align-items: center; justify-content: space-between; }}
    .card-source {{ font-size: 11px; color: var(--text3); }}
    .card-link {{ font-size: 12px; color: var(--accent2); }}
    .tag {{ font-size: 10px; background: #13141c; border: 1px solid var(--border); border-radius: 3px; padding: 2px 6px; color: var(--text2); }}
    .card-tags {{ display: flex; gap: 4px; flex-wrap: wrap; }}
    .empty-state {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 40px; text-align: center; color: var(--text2); }}
    .total-count {{ color: var(--text2); font-size: 14px; margin-bottom: 20px; }}
  </style>
</head>
<body>
  <div class="header">
    <a href="" class="back-link">← Home</a>
    <h1>Intelligence Archive</h1>
  </div>
  <div class="content">
    <p class="total-count">{len(reports)} total reports</p>
    <div class="filters">
      <button class="filter-btn active" onclick="filterByCategory('all')">All</button>
      {category_buttons}
    </div>
    <div class="reports-grid" id="reports-container">
      {cards_html}
    </div>
  </div>
  <script>
    function filterByCategory(cat) {{
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      event.target.classList.add('active');
      document.querySelectorAll('.report-card').forEach(card => {{
        if (cat === 'all' || card.dataset.category === cat) {{
          card.style.display = '';
        }} else {{
          card.style.display = 'none';
        }}
      }});
    }}
  </script>
</body>
</html>"""

    # data-category is now built directly in make_report_card — no post-processing needed

    output_path = PROJECT_ROOT / "reports" / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)
    print(f"  Built: reports/index.html ({len(reports)} reports)")


# ============================================================
# DAILY DIGEST
# ============================================================

def build_daily_digest(reports):
    """Build today's intelligence digest page."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    today_display = datetime.now(timezone.utc).strftime("%B %d, %Y")

    todays_reports = [r for r in reports if r.get("date", "") == today]
    cards_html = "\n".join(make_report_card(r) for r in todays_reports)

    if not cards_html:
        cards_html = f'<div class="empty-state"><p>No intelligence reports for {today_display} yet.</p></div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Daily Intelligence — {today_display}</title>
  <base href="{SITE_BASE}">
  <style>
    :root {{ --bg: #08090e; --surface: #0f1117; --border: #1e2036; --accent: #6366f1; --accent2: #818cf8; --text: #e4e6f0; --text2: #8892b0; --text3: #4b5280; --radius: 12px; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; }}
    a {{ color: var(--accent2); text-decoration: none; }}
    .header {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 16px 24px; display: flex; gap: 16px; align-items: center; }}
    .back-link {{ color: var(--text2); font-size: 14px; }}
    h1 {{ font-size: 20px; font-weight: 700; }}
    .date {{ color: var(--text2); font-size: 14px; }}
    .content {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}
    .reports-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }}
    .report-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; cursor: pointer; transition: border-color 0.2s; }}
    .report-card:hover {{ border-color: var(--accent); }}
    .card-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }}
    .card-meta {{ display: flex; align-items: center; gap: 8px; }}
    .card-category {{ font-size: 11px; background: #13141c; border: 1px solid var(--border); border-radius: 4px; padding: 2px 7px; color: var(--text2); text-transform: uppercase; }}
    .card-date {{ font-size: 12px; color: var(--text3); }}
    .card-score {{ font-size: 16px; font-weight: 700; color: #4ade80; }}
    .card-title {{ font-size: 15px; font-weight: 600; line-height: 1.4; margin-bottom: 10px; }}
    .card-summary {{ font-size: 13px; color: var(--text2); margin-bottom: 14px; }}
    .card-footer {{ display: flex; align-items: center; justify-content: space-between; }}
    .card-source {{ font-size: 11px; color: var(--text3); }}
    .card-link {{ font-size: 12px; color: var(--accent2); }}
    .tag {{ font-size: 10px; background: #13141c; border: 1px solid var(--border); border-radius: 3px; padding: 2px 6px; color: var(--text2); }}
    .card-tags {{ display: flex; gap: 4px; }}
    .empty-state {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 40px; text-align: center; color: var(--text2); }}
  </style>
</head>
<body>
  <div class="header">
    <a href="" class="back-link">← Home</a>
    <h1>Daily Intelligence</h1>
    <span class="date">{today_display}</span>
  </div>
  <div class="content">
    <div class="reports-grid">{cards_html}</div>
  </div>
</body>
</html>"""

    output_path = PROJECT_ROOT / "intelligence" / "daily" / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)
    print(f"  Built: intelligence/daily/index.html ({len(todays_reports)} reports today)")


# ============================================================
# WEEKLY DIGEST
# ============================================================

def build_weekly_digest(reports):
    """Build this week's intelligence digest page."""
    week_start = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
    this_week = [r for r in reports if r.get("date", "") >= week_start]
    cards_html = "\n".join(make_report_card(r) for r in this_week[:20])

    if not cards_html:
        cards_html = '<div class="empty-state"><p>No reports this week yet.</p></div>'

    week_display = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%B %d") + " – " + datetime.now(timezone.utc).strftime("%B %d, %Y")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Weekly Intelligence — {week_display}</title>
  <base href="{SITE_BASE}">
  <style>
    :root {{ --bg: #08090e; --surface: #0f1117; --border: #1e2036; --accent: #6366f1; --accent2: #818cf8; --text: #e4e6f0; --text2: #8892b0; --text3: #4b5280; --radius: 12px; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; }}
    a {{ color: var(--accent2); text-decoration: none; }}
    .header {{ background: var(--surface); border-bottom: 1px solid var(--border); padding: 16px 24px; display: flex; gap: 16px; align-items: center; }}
    .back-link {{ color: var(--text2); font-size: 14px; }}
    h1 {{ font-size: 20px; font-weight: 700; }}
    .week {{ color: var(--text2); font-size: 14px; }}
    .content {{ max-width: 1200px; margin: 0 auto; padding: 32px 24px; }}
    .reports-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }}
    .report-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px; cursor: pointer; transition: border-color 0.2s; }}
    .report-card:hover {{ border-color: var(--accent); }}
    .card-header {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }}
    .card-meta {{ display: flex; align-items: center; gap: 8px; }}
    .card-category {{ font-size: 11px; background: #13141c; border: 1px solid var(--border); border-radius: 4px; padding: 2px 7px; color: var(--text2); text-transform: uppercase; }}
    .card-date {{ font-size: 12px; color: var(--text3); }}
    .card-score {{ font-size: 16px; font-weight: 700; color: #4ade80; }}
    .card-title {{ font-size: 15px; font-weight: 600; line-height: 1.4; margin-bottom: 10px; }}
    .card-summary {{ font-size: 13px; color: var(--text2); margin-bottom: 14px; }}
    .card-footer {{ display: flex; align-items: center; justify-content: space-between; }}
    .card-source {{ font-size: 11px; color: var(--text3); }}
    .card-link {{ font-size: 12px; color: var(--accent2); }}
    .tag {{ font-size: 10px; background: #13141c; border: 1px solid var(--border); border-radius: 3px; padding: 2px 6px; color: var(--text2); }}
    .card-tags {{ display: flex; gap: 4px; }}
    .empty-state {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 40px; text-align: center; color: var(--text2); }}
    .count {{ color: var(--text2); font-size: 14px; margin-bottom: 20px; }}
  </style>
</head>
<body>
  <div class="header">
    <a href="" class="back-link">← Home</a>
    <h1>Weekly Intelligence</h1>
    <span class="week">{week_display}</span>
  </div>
  <div class="content">
    <p class="count">{len(this_week)} reports this week</p>
    <div class="reports-grid">{cards_html}</div>
  </div>
</body>
</html>"""

    output_path = PROJECT_ROOT / "intelligence" / "weekly" / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write(html)
    print(f"  Built: intelligence/weekly/index.html ({len(this_week)} reports this week)")


# ============================================================
# MAIN
# ============================================================

def main():
    print("\n" + "="*60)
    print("STEP 6: BUILDING NAVIGATION INDEXES")
    print("="*60)

    print("\n  Loading all reports...")
    reports = load_all_reports()
    print(f"  Found {len(reports)} reports")

    stats = load_memory_stats()
    print(f"  Memory stats: {stats}")

    print("\n  Building index pages...")
    build_main_index(reports, stats)
    build_reports_archive(reports)
    build_daily_digest(reports)
    build_weekly_digest(reports)

    print("\n" + "="*60)
    print("✓ STEP 6 COMPLETE: All indexes built")
    print("="*60)


if __name__ == "__main__":
    main()
