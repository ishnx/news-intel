#!/usr/bin/env python3
"""
generate_report.py - Beautiful HTML Intelligence Report Generator
=================================================================
Transforms structured analysis JSON into stunning self-contained HTML reports.
Each report is a complete interactive intelligence document with:
- All 20 required analysis sections
- Sticky navigation TOC
- Expandable sections
- Bull/Base/Bear scenario cards
- Entity tags
- Embedded chatbot (uses user's API key from localStorage)
- Reading progress bar

RUN: python scripts/generate_report.py
INPUT: reports/YYYY/MM/DD/*/structured_data.json
OUTPUT: reports/YYYY/MM/DD/*/index.html
NEXT: scripts/update_memory.py
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Site base URL — auto-set by GitHub Actions based on repo name.
# "/" for user/org pages, "/repo-name/" for project pages.
SITE_BASE = os.environ.get("SITE_BASE_URL", "/")

# Hue (0-360) for each category. Drives the entire report's color palette.
CATEGORY_HUE = {
    "ai": 263, "technology": 220, "geopolitics": 38,
    "macro": 174, "india": 25, "energy": 142,
    "finance": 157, "science": 197, "general": 238,
}

CATEGORY_ICONS = {
    "ai": "◈", "technology": "⬡", "geopolitics": "◉",
    "macro": "◐", "india": "◑", "energy": "◈",
    "finance": "◇", "science": "◎", "general": "◈",
}


# ============================================================
# HTML HELPERS
# ============================================================

def esc(text):
    """Escape HTML special characters."""
    if not isinstance(text, str):
        text = str(text)
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def md_to_simple_html(text):
    """Very lightweight markdown-to-HTML converter for report content."""
    if not isinstance(text, str):
        return str(text)
    text = esc(text)
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    # Italic
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    # Inline code
    text = re.sub(r'`(.*?)`', r'<code>\1</code>', text)
    # Paragraphs
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if len(paragraphs) > 1:
        return ''.join(f'<p>{p}</p>' for p in paragraphs)
    return text


def make_section(section_id, title, icon, content_html, accent_color=None):
    """Wrap content in a collapsible section with consistent styling."""
    return f"""<section id="{section_id}" class="intel-section">
  <div class="section-toggle" onclick="toggleSection('{section_id}')">
    <div class="section-heading">
      <span class="section-icon">{icon}</span>
      <h2 class="section-title">{title}</h2>
    </div>
    <span class="toggle-indicator" id="{section_id}-indicator">▾</span>
  </div>
  <div class="section-content" id="{section_id}-content">
    {content_html}
  </div>
</section>"""


def make_player_card(player):
    """Generate an HTML card for a key player."""
    name = esc(player.get("name", "Unknown"))
    role = esc(player.get("role", ""))
    position = esc(player.get("position", ""))
    power = esc(player.get("power", ""))
    return f"""<div class="player-card">
  <div class="player-name">{name}</div>
  <div class="player-role">{role}</div>
  <div class="player-detail"><strong>Position:</strong> {position}</div>
  <div class="player-detail"><strong>Leverage:</strong> {power}</div>
</div>"""


def make_incentive_card(actor_data):
    """Generate a card for a strategic incentive."""
    actor = esc(actor_data.get("actor", ""))
    incentive = esc(actor_data.get("incentive", ""))
    constraint = esc(actor_data.get("constraint", ""))
    likely = esc(actor_data.get("likely_action", ""))
    return f"""<div class="incentive-card">
  <div class="incentive-actor">{actor}</div>
  <div class="incentive-row"><span class="incentive-label">Goal</span><span>{incentive}</span></div>
  <div class="incentive-row"><span class="incentive-label">Constraint</span><span>{constraint}</span></div>
  <div class="incentive-row likely"><span class="incentive-label">Likely Action</span><span>{likely}</span></div>
</div>"""


def make_analogy_card(analogy_data):
    """Generate an HTML card for a historical analogy."""
    analogy = esc(analogy_data.get("analogy", ""))
    period = esc(analogy_data.get("period", ""))
    what = esc(analogy_data.get("what_happened", ""))
    lesson = esc(analogy_data.get("lesson", ""))
    breaks = esc(analogy_data.get("where_analogy_breaks", ""))
    return f"""<div class="analogy-card">
  <div class="analogy-header">
    <span class="analogy-period">{period}</span>
    <span class="analogy-title">{analogy}</span>
  </div>
  <p class="analogy-what">{what}</p>
  <div class="analogy-lesson"><strong>Lesson:</strong> {lesson}</div>
  <div class="analogy-breaks"><strong>Where analogy breaks:</strong> {breaks}</div>
</div>"""


def make_scenario_card(scenario_data, scenario_type):
    """Generate a Bull/Base/Bear scenario card."""
    colors = {"bull": "#4ade80", "base": "#fbbf24", "bear": "#f87171"}
    labels = {"bull": "BULL CASE", "base": "BASE CASE", "bear": "BEAR CASE"}
    icons = {"bull": "↑", "base": "→", "bear": "↓"}

    color = colors.get(scenario_type, "#8892b0")
    label = labels.get(scenario_type, scenario_type.upper())
    icon = icons.get(scenario_type, "•")
    title = esc(scenario_data.get("title", ""))
    description = md_to_simple_html(scenario_data.get("description", ""))
    probability = esc(scenario_data.get("probability", "?"))
    indicators = scenario_data.get("indicators", [])

    indicators_html = ""
    if indicators:
        items = "".join(f'<li>{esc(ind)}</li>' for ind in indicators)
        indicators_html = f'<div class="scenario-indicators"><div class="scenario-signals-label">Watch for:</div><ul>{items}</ul></div>'

    return f"""<div class="scenario-card" style="border-top: 3px solid {color}">
  <div class="scenario-header">
    <span class="scenario-label" style="color: {color}">{icon} {label}</span>
    <span class="scenario-prob" style="color: {color}">{probability}</span>
  </div>
  <div class="scenario-title">{title}</div>
  <div class="scenario-desc">{description}</div>
  {indicators_html}
</div>"""


def make_contrarian_card(view_data):
    """Generate a contrarian perspective card."""
    view = md_to_simple_html(view_data.get("view", ""))
    reasoning = md_to_simple_html(view_data.get("reasoning", ""))
    confidence = view_data.get("confidence", "medium")
    conf_colors = {"low": "#8892b0", "medium": "#fbbf24", "high": "#4ade80"}
    conf_color = conf_colors.get(confidence, "#fbbf24")
    return f"""<div class="contrarian-card">
  <div class="contrarian-badge" style="color: {conf_color}">⊗ {confidence.upper()} CONFIDENCE</div>
  <div class="contrarian-view">{view}</div>
  <div class="contrarian-reasoning"><strong>Why this might be right:</strong> {reasoning}</div>
</div>"""


def make_entity_tag(entity):
    """Generate a clickable entity tag."""
    name = esc(entity.get("name", ""))
    etype = entity.get("type", "entity")
    significance = esc(entity.get("significance", ""))
    type_colors = {
        "person": "#818cf8", "company": "#34d399", "country": "#fbbf24",
        "technology": "#f472b6", "institution": "#60a5fa"
    }
    color = type_colors.get(etype.lower(), "#8892b0")
    return f'<span class="entity-tag" style="border-color: {color}" title="{significance}">{name}</span>'


# ============================================================
# CSS STYLES
# ============================================================

REPORT_CSS = """
/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   World Intel — Luxury Intelligence Report Design
   Category color injected as --cat-h (hue 0-360) per report
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
:root {
  /* Contextual — overridden per-report via inline <style> */
  --cat-h: 238;
  --cat:        hsl(var(--cat-h), 72%, 65%);
  --cat-dim:    hsl(var(--cat-h), 55%, 52%);
  --cat-soft:   hsla(var(--cat-h), 72%, 65%, 0.12);
  --cat-glow:   hsla(var(--cat-h), 72%, 65%, 0.05);
  --cat-border: hsla(var(--cat-h), 72%, 65%, 0.20);

  /* Base */
  --bg:      #07070e;
  --surface: #0d0d18;
  --surface2:#121220;
  --surface3:#181828;

  /* Borders */
  --border:  rgba(255,255,255,0.065);
  --border2: rgba(255,255,255,0.11);

  /* Text */
  --text:  #eeeef8;
  --text2: #7a82ac;
  --text3: #404568;

  /* Signals */
  --bull:    #4ade80;
  --bear:    #f87171;
  --neutral: #fbbf24;

  /* Shape */
  --r:    12px;
  --r-sm: 7px;
  --r-lg: 18px;

  /* Layout */
  --header-h: 52px;
  --toc-w:    212px;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body {
  background: var(--bg); color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
  line-height: 1.65; font-size: 15px;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--cat); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ── PROGRESS ── */
#progress-bar {
  position: fixed; top: 0; left: 0; width: 0%; height: 2px;
  background: linear-gradient(90deg, var(--cat-dim), var(--cat));
  z-index: 9999; transition: width 0.1s linear;
  box-shadow: 0 0 10px var(--cat-soft);
}

/* ── HEADER ── */
.report-header {
  background: rgba(7,7,14,0.84);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-bottom: 1px solid var(--border);
  padding: 0 24px; position: sticky; top: 0; z-index: 90;
  height: var(--header-h); display: flex; align-items: center; gap: 14px;
}
.back-btn { color: var(--text3); font-size: 13px; white-space: nowrap; transition: color 0.15s; }
.back-btn:hover { color: var(--text2); text-decoration: none; }
.header-title { flex: 1; font-size: 13px; font-weight: 500; color: var(--text3); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.header-badge {
  font-size: 10px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase;
  background: var(--cat-soft); color: var(--cat);
  border: 1px solid var(--cat-border); padding: 3px 10px; border-radius: 20px; white-space: nowrap;
}
.header-date { font-size: 11px; color: var(--text3); white-space: nowrap; }

/* ── LAYOUT ── */
.layout { display: flex; max-width: 1300px; margin: 0 auto; min-height: calc(100vh - var(--header-h)); }

/* ── TOC ── */
.toc-sidebar {
  width: var(--toc-w); flex-shrink: 0;
  position: sticky; top: var(--header-h);
  height: calc(100vh - var(--header-h));
  overflow-y: auto; padding: 28px 0 28px 4px;
  border-right: 1px solid var(--border);
}
.toc-sidebar::-webkit-scrollbar { width: 2px; }
.toc-sidebar::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 1px; }
.toc-title { font-size: 9px; font-weight: 700; letter-spacing: 1.8px; text-transform: uppercase; color: var(--text3); margin-bottom: 10px; padding: 0 12px; }
.toc-item {
  display: block; font-size: 11.5px; color: var(--text3);
  padding: 5px 14px; border-radius: var(--r-sm);
  margin: 0 4px 1px; cursor: pointer; transition: all 0.14s;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.toc-item:hover { color: var(--text2); background: var(--surface2); }
.toc-item.active { background: var(--cat-soft); color: var(--cat); font-weight: 500; }

/* ── MAIN ── */
.main-content { flex: 1; max-width: 800px; min-width: 0; padding-bottom: 80px; }

/* ── HERO ── */
.report-hero {
  position: relative; padding: 52px 52px 40px;
  border-bottom: 1px solid var(--border); overflow: hidden;
}
.hero-glow {
  position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(ellipse 80% 200% at 50% -30%, var(--cat-soft) 0%, transparent 65%);
}
.hero-eyebrow {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 20px; position: relative; z-index: 1;
}
.hero-chip {
  font-size: 10px; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase;
  background: var(--cat-soft); color: var(--cat);
  border: 1px solid var(--cat-border); padding: 4px 11px; border-radius: 20px;
}
.hero-dot { color: var(--text3); font-size: 10px; }
.hero-source { font-size: 12px; color: var(--text3); }
.hero-date-text { font-size: 12px; color: var(--text3); }
.report-title {
  font-size: 42px; font-weight: 700; line-height: 1.12;
  letter-spacing: -0.8px; color: var(--text);
  margin-bottom: 28px; position: relative; z-index: 1;
}
.hero-metrics {
  display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
  margin-bottom: 18px; position: relative; z-index: 1;
}
.score-badge {
  display: flex; align-items: baseline; gap: 6px;
  background: var(--cat-soft); border: 1px solid var(--cat-border);
  border-radius: 8px; padding: 7px 14px;
}
.score-value { font-size: 22px; font-weight: 700; color: var(--cat); line-height: 1; }
.score-label { font-size: 9px; font-weight: 600; letter-spacing: 0.6px; text-transform: uppercase; color: var(--text3); }
.conf-badge {
  font-size: 11px; color: var(--text3);
  border: 1px solid var(--border); border-radius: 8px; padding: 7px 12px;
}
.src-link {
  font-size: 11px; color: var(--cat); font-weight: 500;
  border: 1px solid var(--cat-border); border-radius: 8px; padding: 7px 12px;
  transition: background 0.15s;
}
.src-link:hover { background: var(--cat-soft); text-decoration: none; }
.report-tags { display: flex; gap: 6px; flex-wrap: wrap; position: relative; z-index: 1; }
.report-tag {
  font-size: 10px; font-weight: 500;
  background: var(--surface2); border: 1px solid var(--border2);
  color: var(--text3); padding: 4px 10px; border-radius: 20px;
}

/* ── EXEC SUMMARY CARD ── */
.exec-card {
  margin: 32px 52px;
  background: linear-gradient(135deg, var(--cat-glow), transparent);
  border: 1px solid var(--cat-border); border-radius: var(--r-lg);
  padding: 28px 32px;
}
.exec-label {
  font-size: 9px; font-weight: 700; letter-spacing: 1.5px; text-transform: uppercase;
  color: var(--cat); margin-bottom: 14px;
}
.exec-text { font-size: 16px; line-height: 1.82; color: var(--text); }
.exec-text p { margin-bottom: 14px; }
.exec-text p:last-child { margin-bottom: 0; }
.exec-text strong { font-weight: 600; }

/* ── INTEL SECTIONS ── */
.intel-section { border-bottom: 1px solid var(--border); }
.section-toggle {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 52px; cursor: pointer; user-select: none;
  transition: background 0.14s;
}
.section-toggle:hover { background: rgba(255,255,255,0.016); }
.section-heading { display: flex; align-items: center; gap: 11px; }
.section-icon { font-size: 15px; opacity: 0.7; }
.section-title { font-size: 14px; font-weight: 600; color: var(--text2); }
.section-toggle:hover .section-title { color: var(--text); }
.toggle-indicator { color: var(--text3); font-size: 13px; transition: transform 0.18s ease; }
.toggle-indicator.collapsed { transform: rotate(-90deg); }
.section-content { padding: 4px 52px 28px; }
.section-content.collapsed { display: none; }

/* ── PROSE ── */
.prose { font-size: 14px; color: var(--text2); line-height: 1.82; }
.prose p { margin-bottom: 13px; }
.prose p:last-child { margin-bottom: 0; }
.prose strong { color: var(--text); font-weight: 600; }
.prose code { background: var(--surface2); padding: 1px 5px; border-radius: 4px; font-size: 12px; }

/* ── LISTS ── */
.intel-list { list-style: none; }
.intel-list li {
  padding: 10px 0 10px 20px; border-bottom: 1px solid var(--border);
  color: var(--text2); font-size: 14px; position: relative; line-height: 1.7;
}
.intel-list li:last-child { border-bottom: none; }
.intel-list li::before { content: '›'; position: absolute; left: 0; color: var(--cat); font-size: 16px; line-height: 1.55; font-weight: 300; }

/* ── PLAYER CARDS ── */
.cards-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; }
.player-card {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: var(--r); padding: 16px; transition: border-color 0.14s, transform 0.14s;
}
.player-card:hover { border-color: var(--border2); transform: translateY(-1px); }
.player-name { font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 3px; }
.player-role { font-size: 11px; color: var(--cat); font-weight: 500; margin-bottom: 11px; }
.player-detail { font-size: 12px; color: var(--text2); margin-bottom: 5px; line-height: 1.5; }
.player-detail strong { color: var(--text3); font-weight: 600; font-size: 10px; text-transform: uppercase; letter-spacing: 0.3px; }

/* ── INCENTIVE CARDS ── */
.incentive-card {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: var(--r); padding: 16px; margin-bottom: 10px;
}
.incentive-actor { font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 12px; padding-bottom: 10px; border-bottom: 1px solid var(--border); }
.incentive-row { display: flex; gap: 12px; margin-bottom: 7px; font-size: 13px; color: var(--text2); }
.incentive-label { min-width: 80px; font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text3); padding-top: 2px; flex-shrink: 0; }
.incentive-row.likely { background: var(--cat-glow); border-radius: var(--r-sm); padding: 9px 11px; margin-top: 4px; border: 1px solid var(--cat-border); }

/* ── ANALOGY CARDS ── */
.analogy-card {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: var(--r); padding: 18px; margin-bottom: 10px;
}
.analogy-header { display: flex; align-items: baseline; gap: 10px; margin-bottom: 10px; }
.analogy-period { font-size: 9px; font-weight: 700; color: var(--cat); text-transform: uppercase; letter-spacing: 0.8px; }
.analogy-title { font-size: 14px; font-weight: 600; color: var(--text); }
.analogy-what { font-size: 13px; color: var(--text2); margin-bottom: 12px; line-height: 1.7; }
.analogy-lesson {
  font-size: 13px; color: var(--text2); padding: 10px 14px;
  background: var(--cat-glow); border-radius: var(--r-sm);
  border-left: 2px solid var(--cat); margin-bottom: 8px;
}
.analogy-breaks { font-size: 12px; color: var(--text3); font-style: italic; }

/* ── SCENARIO CARDS ── */
.scenarios-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.scenario-card {
  background: var(--surface2); border: 1px solid var(--border); border-radius: var(--r);
  padding: 16px; display: flex; flex-direction: column; gap: 9px;
}
.scenario-header { display: flex; justify-content: space-between; align-items: center; }
.scenario-label { font-size: 9px; font-weight: 700; letter-spacing: 0.8px; text-transform: uppercase; }
.scenario-prob { font-size: 13px; font-weight: 700; }
.scenario-title { font-size: 13px; font-weight: 600; color: var(--text); }
.scenario-desc { font-size: 12px; color: var(--text2); line-height: 1.7; }
.scenario-signals-label { font-size: 9px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text3); margin-bottom: 5px; }
.scenario-indicators ul { list-style: none; }
.scenario-indicators li { font-size: 11px; color: var(--text3); padding: 2px 0 2px 12px; position: relative; }
.scenario-indicators li::before { content: '—'; position: absolute; left: 0; font-size: 10px; }

/* ── CONTRARIAN ── */
.contrarian-card {
  background: var(--surface2); border: 1px solid var(--border);
  border-radius: var(--r); padding: 18px; margin-bottom: 10px;
}
.contrarian-badge { font-size: 9px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 10px; }
.contrarian-view { font-size: 14px; color: var(--text); margin-bottom: 10px; line-height: 1.75; font-style: italic; }
.contrarian-reasoning { font-size: 13px; color: var(--text2); line-height: 1.7; }

/* ── ENTITY TAGS ── */
.entities-container { display: flex; flex-wrap: wrap; gap: 8px; }
.entity-tag {
  font-size: 12px; color: var(--text); padding: 5px 12px;
  border: 1px solid; border-radius: 20px; background: var(--surface2);
  cursor: default; transition: background 0.14s;
}
.entity-tag:hover { background: var(--surface3); }

/* ── QUESTIONS ── */
.questions-list { list-style: none; }
.question-item {
  background: var(--surface2); border: 1px solid var(--border); border-radius: var(--r-sm);
  padding: 11px 16px; margin-bottom: 6px; font-size: 13px; color: var(--text2);
  cursor: pointer; transition: all 0.14s; display: flex; gap: 9px; line-height: 1.6;
}
.question-item:hover { border-color: var(--cat-border); color: var(--text); background: var(--cat-glow); }
.question-item::before { content: '?'; color: var(--cat); font-weight: 700; flex-shrink: 0; }

/* ── UNKNOWNS ── */
.unknowns-list { list-style: none; }
.unknown-item {
  padding: 10px 0 10px 22px; border-bottom: 1px solid var(--border);
  color: var(--text2); font-size: 14px; position: relative; line-height: 1.7;
}
.unknown-item:last-child { border-bottom: none; }
.unknown-item::before { content: '⚠'; position: absolute; left: 0; top: 12px; color: var(--neutral); font-size: 11px; }

/* ── CHATBOT TOGGLE ── */
#chatbot-toggle {
  position: fixed; bottom: 24px; right: 24px; z-index: 1000;
  background: var(--cat); color: white; border: none;
  border-radius: 50px; padding: 11px 22px; font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all 0.2s ease;
  box-shadow: 0 4px 20px var(--cat-soft), 0 0 0 1px var(--cat-border);
}
#chatbot-toggle:hover { filter: brightness(1.1); transform: translateY(-2px); }

/* ── CHATBOT PANEL ── */
#chatbot-panel {
  position: fixed; bottom: 0; right: 0; z-index: 999;
  width: 400px; max-width: 100vw; height: 580px; max-height: 90vh;
  background: rgba(8,8,18,0.92);
  backdrop-filter: blur(28px) saturate(160%);
  -webkit-backdrop-filter: blur(28px) saturate(160%);
  border-top: 1px solid var(--border2); border-left: 1px solid var(--border2);
  border-radius: 16px 0 0 0; display: flex; flex-direction: column;
  box-shadow: -6px 0 40px rgba(0,0,0,0.7);
  transform: translateX(105%); transition: transform 0.3s cubic-bezier(0.32,0.72,0,1);
}
#chatbot-panel.open { transform: translateX(0); }
.chatbot-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 13px 15px; border-bottom: 1px solid var(--border); flex-shrink: 0;
}
.chatbot-title { font-size: 13px; font-weight: 600; }
.chatbot-close { background: none; border: none; color: var(--text3); cursor: pointer; font-size: 18px; padding: 2px 4px; transition: color 0.14s; }
.chatbot-close:hover { color: var(--text); }
.chatbot-key-status { font-size: 10px; padding: 2px 7px; border-radius: 10px; }
.chatbot-key-status.set { background: rgba(74,222,128,0.12); color: var(--bull); }
.chatbot-key-status.unset { background: rgba(248,113,113,0.12); color: var(--bear); }
#chat-messages { flex: 1; overflow-y: auto; padding: 14px 15px; display: flex; flex-direction: column; gap: 9px; }
#chat-messages::-webkit-scrollbar { width: 2px; }
#chat-messages::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 1px; }
.chat-message { max-width: 88%; padding: 9px 12px; border-radius: 12px; font-size: 12.5px; line-height: 1.65; }
.chat-message.user { background: var(--cat-soft); color: var(--text); align-self: flex-end; border: 1px solid var(--cat-border); border-radius: 12px 12px 3px 12px; }
.chat-message.assistant { background: var(--surface2); border: 1px solid var(--border); color: var(--text2); align-self: flex-start; border-radius: 12px 12px 12px 3px; }
.chat-message.system { color: var(--text3); font-size: 11px; align-self: center; font-style: italic; max-width: 100%; text-align: center; }
.chat-thinking { display: flex; gap: 4px; align-items: center; padding: 9px 12px; }
.chat-thinking span { width: 5px; height: 5px; background: var(--text3); border-radius: 50%; animation: bounce 1.2s infinite; }
.chat-thinking span:nth-child(2) { animation-delay: 0.2s; }
.chat-thinking span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-5px)} }
.suggested-questions { padding: 0 12px 8px; flex-shrink: 0; }
.sq-label { font-size: 9px; color: var(--text3); margin-bottom: 5px; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 700; }
.sq-btn { display: block; width: 100%; text-align: left; background: var(--surface2); border: 1px solid var(--border); color: var(--text2); border-radius: 6px; padding: 6px 10px; font-size: 11px; cursor: pointer; margin-bottom: 3px; transition: all 0.14s; line-height: 1.4; }
.sq-btn:hover { border-color: var(--cat-border); color: var(--text); background: var(--cat-glow); }
#chatbot-api-setup { padding: 10px 12px; border-top: 1px solid var(--border); background: rgba(248,113,113,0.04); flex-shrink: 0; }
.api-setup-label { font-size: 10px; color: var(--text3); margin-bottom: 5px; }
.api-setup-row { display: flex; gap: 6px; }
#api-key-input { flex: 1; background: var(--surface2); border: 1px solid var(--border); color: var(--text); border-radius: 6px; padding: 7px 10px; font-size: 12px; }
#api-key-save { background: var(--cat); color: white; border: none; border-radius: 6px; padding: 7px 14px; font-size: 12px; cursor: pointer; font-weight: 600; }
.chatbot-input-area { display: flex; gap: 8px; padding: 12px; border-top: 1px solid var(--border); flex-shrink: 0; }
#chat-input { flex: 1; background: var(--surface2); border: 1px solid var(--border); color: var(--text); border-radius: 8px; padding: 9px 14px; font-size: 13px; height: 40px; }
#chat-input:focus { outline: none; border-color: var(--cat-border); }
#chat-send { background: var(--cat); color: white; border: none; border-radius: 8px; padding: 9px 16px; cursor: pointer; font-size: 13px; font-weight: 600; }
#chat-send:hover { filter: brightness(1.1); }

/* ── CHATBOT EXTENDED ── */
.status-badge { font-size: 10px; padding: 2px 7px; border-radius: 10px; cursor: default; white-space: nowrap; }
.github-connected { background: rgba(74,222,128,0.12); color: var(--bull); }
.github-disconnected { background: rgba(100,116,139,0.12); color: var(--text3); }
#memory-counter { font-size: 10px; padding: 2px 7px; border-radius: 10px; background: var(--cat-soft); color: var(--cat); display: none; }
#settings-panel { padding: 11px 13px; border-bottom: 1px solid var(--border); background: var(--cat-glow); display: none; flex-shrink: 0; }
.settings-row { margin-bottom: 7px; }
.settings-label { font-size: 9px; color: var(--text3); margin-bottom: 3px; text-transform: uppercase; letter-spacing: 0.4px; font-weight: 600; }
.settings-input { width: 100%; background: var(--surface2); border: 1px solid var(--border); color: var(--text); border-radius: 6px; padding: 6px 9px; font-size: 12px; }
.settings-input:focus { outline: none; border-color: var(--cat-border); }
.settings-save-btn { width: 100%; background: var(--cat); color: white; border: none; border-radius: 6px; padding: 7px; font-size: 12px; cursor: pointer; margin-top: 4px; font-weight: 600; }
.chatbot-actions { display: flex; gap: 6px; padding: 5px 11px; border-bottom: 1px solid var(--border); flex-shrink: 0; }
.chatbot-action-btn { font-size: 10px; background: var(--surface2); border: 1px solid var(--border); color: var(--text2); border-radius: 6px; padding: 4px 9px; cursor: pointer; transition: all 0.14s; }
.chatbot-action-btn:hover { border-color: var(--cat-border); color: var(--text); }
.copyable-insights { max-width: 100% !important; align-self: stretch !important; }
.copy-label { font-size: 9px; color: var(--text3); margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.3px; }
.copy-textarea { width: 100%; background: var(--surface); border: 1px solid var(--border); color: var(--text2); border-radius: 6px; padding: 7px; font-size: 11px; font-family: monospace; resize: vertical; min-height: 80px; }
.copy-btn { margin-top: 4px; background: var(--surface2); border: 1px solid var(--border); color: var(--text2); border-radius: 6px; padding: 4px 12px; font-size: 10px; cursor: pointer; }
.chatbot-gear { background: none; border: none; color: var(--text3); cursor: pointer; font-size: 13px; padding: 2px 4px; transition: color 0.14s; }
.chatbot-gear:hover { color: var(--text); }

/* ── FOOTER ── */
.report-footer { padding: 28px 52px; color: var(--text3); font-size: 11px; border-top: 1px solid var(--border); line-height: 1.7; }

/* ── RESPONSIVE ── */
@media (max-width: 920px) {
  .toc-sidebar { display: none; }
  .report-hero { padding: 32px 24px 28px; }
  .report-title { font-size: 28px; }
  .section-toggle { padding: 18px 24px; }
  .section-content { padding: 4px 24px 24px; }
  .exec-card { margin: 20px 24px; padding: 20px 22px; }
  .scenarios-grid { grid-template-columns: 1fr; }
  #chatbot-panel { width: 100%; border-left: none; border-radius: 16px 16px 0 0; }
  .report-footer { padding: 24px; }
}
@media print {
  #progress-bar, .report-header, .toc-sidebar, #chatbot-toggle, #chatbot-panel { display: none !important; }
  .intel-section { page-break-inside: avoid; }
  .section-content.collapsed { display: block !important; }
}
"""

# ============================================================
# JAVASCRIPT
# ============================================================

REPORT_JS = """
// ─── CONFIGURATION ───
const MEMORY_KEY = 'intel_insights';
const SETTINGS_KEY = 'intel_settings';
let chatOpen = false;
let settingsOpen = false;
let chatHistory = [];
const REPORT_DATA = window._REPORT_DATA || {};
const WORLDVIEW = window._WORLDVIEW_CONTEXT || '';

// ─── READING PROGRESS ───
window.addEventListener('scroll', () => {
  const scrolled = window.scrollY;
  const total = document.documentElement.scrollHeight - window.innerHeight;
  const pct = total > 0 ? (scrolled / total) * 100 : 0;
  document.getElementById('progress-bar').style.width = pct + '%';
  updateTOC();
});

// ─── SECTION TOGGLE ───
function toggleSection(sectionId) {
  const content = document.getElementById(sectionId + '-content');
  const indicator = document.getElementById(sectionId + '-indicator');
  if (!content) return;
  const isCollapsed = content.classList.toggle('collapsed');
  if (indicator) indicator.classList.toggle('collapsed', isCollapsed);
}

// ─── TOC ACTIVE SECTION ───
function updateTOC() {
  const sections = document.querySelectorAll('.intel-section');
  const tocItems = document.querySelectorAll('.toc-item');
  let currentActive = null;
  sections.forEach(section => {
    const rect = section.getBoundingClientRect();
    if (rect.top <= 100) currentActive = section.id;
  });
  tocItems.forEach(item => {
    item.classList.toggle('active', item.dataset.section === currentActive);
  });
}

function scrollToSection(sectionId) {
  const el = document.getElementById(sectionId);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ─── LOCAL MEMORY (persists insights across browser sessions) ───
function getLocalInsights() {
  try { return JSON.parse(localStorage.getItem(MEMORY_KEY) || '[]'); }
  catch(e) { return []; }
}

function saveInsightLocally(insight) {
  const all = getLocalInsights();
  all.push(Object.assign({}, insight, { savedAt: new Date().toISOString() }));
  if (all.length > 200) all.splice(0, all.length - 200);
  localStorage.setItem(MEMORY_KEY, JSON.stringify(all));
  updateMemoryCounter();
}

function updateMemoryCounter() {
  const count = getLocalInsights().length;
  const el = document.getElementById('memory-counter');
  if (!el) return;
  el.style.display = count > 0 ? 'inline' : 'none';
  el.textContent = count + ' insights';
}

// ─── GITHUB SETTINGS ───
function getGitHubSettings() {
  try { return JSON.parse(localStorage.getItem(SETTINGS_KEY) || '{}'); }
  catch(e) { return {}; }
}

function toggleSettings() {
  settingsOpen = !settingsOpen;
  const panel = document.getElementById('settings-panel');
  if (!panel) return;
  panel.style.display = settingsOpen ? 'block' : 'none';
  if (settingsOpen) {
    const s = getGitHubSettings();
    const repoEl = document.getElementById('gh-repo-input');
    const branchEl = document.getElementById('gh-branch-input');
    if (repoEl && s.repo) repoEl.value = s.repo;
    if (branchEl && s.branch) branchEl.value = s.branch;
  }
}

function saveGitHubSettings() {
  const pat = (document.getElementById('gh-pat-input') || {}).value || '';
  const repo = (document.getElementById('gh-repo-input') || {}).value || '';
  const branch = ((document.getElementById('gh-branch-input') || {}).value || 'main').trim();
  if (!pat.trim() || !repo.trim()) {
    addMessage('system', 'Enter both a GitHub PAT and repository name (owner/repo).');
    return;
  }
  localStorage.setItem(SETTINGS_KEY, JSON.stringify({ pat: pat.trim(), repo: repo.trim(), branch }));
  addMessage('system', '✓ GitHub connected. Insights will auto-commit to ' + repo.trim() + '/memory/');
  updateGitHubStatus();
  settingsOpen = false;
  const panel = document.getElementById('settings-panel');
  if (panel) panel.style.display = 'none';
}

function updateGitHubStatus() {
  const s = getGitHubSettings();
  const el = document.getElementById('github-status');
  if (!el) return;
  if (s.pat && s.repo) {
    el.textContent = '⬡ ' + s.repo.split('/').slice(-1)[0];
    el.className = 'status-badge github-connected';
    el.title = 'GitHub: ' + s.repo;
  } else {
    el.textContent = '⬡ GitHub';
    el.className = 'status-badge github-disconnected';
    el.title = 'Click ⚙ to connect GitHub for auto-commit';
  }
}

// ─── GITHUB CONTENTS API (commits insights directly to the repo) ───
async function commitToGitHub(appendContent, filePath, commitMessage) {
  const s = getGitHubSettings();
  if (!s.pat || !s.repo) return false;

  const branch = s.branch || 'main';
  const apiUrl = 'https://api.github.com/repos/' + s.repo + '/contents/' + filePath;
  const headers = {
    'Authorization': 'token ' + s.pat,
    'Content-Type': 'application/json',
    'Accept': 'application/vnd.github.v3+json'
  };

  let sha = null;
  let newContent = appendContent;

  try {
    const getResp = await fetch(apiUrl + '?ref=' + branch, { headers: headers });
    if (getResp.ok) {
      const fileData = await getResp.json();
      sha = fileData.sha;
      // Decode existing content and append new insights
      const existing = decodeURIComponent(escape(atob(fileData.content.replace(/\\n/g, ''))));
      newContent = existing + appendContent;
    }
  } catch(e) { /* file may not exist yet — will be created */ }

  const encoded = btoa(unescape(encodeURIComponent(newContent)));
  const body = { message: commitMessage, content: encoded, branch: branch };
  if (sha) body.sha = sha;

  try {
    const resp = await fetch(apiUrl, {
      method: 'PUT', headers: headers, body: JSON.stringify(body)
    });
    return resp.ok;
  } catch(e) {
    console.error('GitHub commit error:', e);
    return false;
  }
}

// ─── INSIGHT EXTRACTION (Claude Haiku mines conversation → memory) ───
async function extractAndSaveInsights(silent) {
  const apiKey = localStorage.getItem('anthropic_api_key');
  if (!apiKey || chatHistory.length < 2) {
    if (!silent) addMessage('system', 'Have a conversation first, then extract insights.');
    return;
  }
  if (!silent) addMessage('system', '🔍 Mining conversation for insights...');

  const conversationText = chatHistory
    .map(function(m) { return m.role.toUpperCase() + ': ' + m.content; })
    .join('\\n\\n');

  const extractPrompt = 'You are extracting structured intelligence insights from a conversation.\\n\\n' +
    'STORY: ' + (REPORT_DATA.metadata && REPORT_DATA.metadata.title ? REPORT_DATA.metadata.title : 'Unknown') + '\\n\\n' +
    'CONVERSATION:\\n' + conversationText + '\\n\\n' +
    'Return ONLY valid JSON (no markdown):\\n' +
    '{"new_facts": ["..."], "open_questions": ["..."], "patterns": ["..."], "connections": ["..."]}\\n\\n' +
    'Rules: max 3 items per category; only include insights NOT in the original report; empty arrays are fine.';

  try {
    const resp = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true'
      },
      body: JSON.stringify({
        model: 'claude-haiku-4-5-20251001',
        max_tokens: 512,
        messages: [{ role: 'user', content: extractPrompt }]
      })
    });

    const data = await resp.json();
    if (data.error || !data.content) return;

    let extracted;
    try {
      const text = (data.content[0] || {}).text || '{}';
      const match = text.match(/\\{[\\s\\S]*\\}/);
      extracted = JSON.parse(match ? match[0] : '{}');
    } catch(e) { return; }

    const pathParts = window.location.pathname.split('/').filter(Boolean);
    const storySlug = pathParts.slice(-2).join('/') || 'unknown';
    const date = new Date().toISOString().slice(0, 10);
    let savedCount = 0;
    let memoryMd = '';
    let questionsMd = '';

    ['new_facts', 'patterns', 'connections'].forEach(function(type) {
      const items = extracted[type] || [];
      items.forEach(function(item) {
        if (item && item.length > 10) {
          saveInsightLocally({ type: type, content: item, story: storySlug, date: date });
          memoryMd += '- **' + date + '** [chat/' + storySlug + ']: ' + item + '\\n';
          savedCount++;
        }
      });
    });

    (extracted.open_questions || []).forEach(function(q) {
      if (q && q.length > 10) {
        saveInsightLocally({ type: 'question', content: q, story: storySlug, date: date });
        questionsMd += '- **' + date + '** [chat/' + storySlug + ']: ' + q + '\\n';
        savedCount++;
      }
    });

    if (savedCount === 0) {
      if (!silent) addMessage('system', 'No new insights beyond the original report found.');
      return;
    }

    const s = getGitHubSettings();
    if (s.pat && s.repo) {
      const msg = 'memory: ' + savedCount + ' insights from chat ' + date;
      const ok1 = memoryMd ? await commitToGitHub('\\n' + memoryMd, 'memory/master_memory.md', msg) : true;
      const ok2 = questionsMd ? await commitToGitHub('\\n' + questionsMd, 'memory/unresolved_questions.md', msg) : true;
      if (!silent) {
        if (ok1 || ok2) {
          addMessage('system', '✓ ' + savedCount + ' insights committed to ' + s.repo + '/memory/');
        } else {
          addMessage('system', '⚠ GitHub commit failed. Insights saved locally.');
          showCopyableInsights(memoryMd, questionsMd);
        }
      }
    } else {
      if (!silent) {
        addMessage('system', '✓ ' + savedCount + ' insights saved locally. Connect GitHub (⚙) to auto-commit.');
        showCopyableInsights(memoryMd, questionsMd);
      }
    }

  } catch(e) {
    if (!silent) addMessage('system', 'Extraction error: ' + e.message);
  }
}

function showCopyableInsights(memoryMd, questionsMd) {
  if (!memoryMd && !questionsMd) return;
  const msgs = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-message system copyable-insights';
  const combined = (memoryMd ? '# Add to memory/master_memory.md\\n' + memoryMd : '') +
    (questionsMd ? '\\n# Add to memory/unresolved_questions.md\\n' + questionsMd : '');
  const safe = combined.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  div.innerHTML = '<div class="copy-label">Paste into your memory files:</div>' +
    '<textarea class="copy-textarea" readonly>' + safe + '</textarea>' +
    '<button onclick="this.previousElementSibling.select();document.execCommand(\\'copy\\');this.textContent=\\'Copied!\\'" class="copy-btn">Copy</button>';
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

// ─── SYSTEM PROMPT (enriched with accumulated memory each session) ───
function buildChatSystemPrompt() {
  const insights = getLocalInsights().slice(-30);
  let insightsBlock = '';
  if (insights.length > 0) {
    insightsBlock = '\\n\\nACCUMULATED INSIGHTS FROM YOUR PREVIOUS SESSIONS:\\n';
    insights.forEach(function(i) {
      insightsBlock += '[' + i.type + '] ' + i.content + ' (from: ' + i.story + ', ' + i.date + ')\\n';
    });
  }

  const title = REPORT_DATA.metadata && REPORT_DATA.metadata.title ? REPORT_DATA.metadata.title : 'Unknown';
  const source = REPORT_DATA.metadata && REPORT_DATA.metadata.source_name ? REPORT_DATA.metadata.source_name : 'Unknown';
  const pubDate = REPORT_DATA.metadata && REPORT_DATA.metadata.published_at ? REPORT_DATA.metadata.published_at.slice(0, 10) : 'Unknown';
  const category = REPORT_DATA.metadata && REPORT_DATA.metadata.category ? REPORT_DATA.metadata.category : 'Unknown';
  const analysisJson = JSON.stringify(REPORT_DATA.analysis || {}, null, 2).slice(0, 7000);

  return 'You are an elite intelligence analyst embedded in a living, self-improving intelligence system.\\n\\n' +
    'CURRENT REPORT:\\n' +
    'Title: ' + title + '\\n' +
    'Source: ' + source + '\\n' +
    'Date: ' + pubDate + '\\n' +
    'Category: ' + category + '\\n\\n' +
    'FULL ANALYSIS (JSON):\\n' + analysisJson + '\\n\\n' +
    'WORLDVIEW CONTEXT:\\n' + WORLDVIEW.slice(0, 2000) +
    insightsBlock + '\\n\\n' +
    'YOUR ROLE:\\n' +
    '- Answer with the precision of a world-class geopolitical and financial analyst\\n' +
    '- Reference accumulated insights from past sessions when relevant\\n' +
    '- Surface non-obvious connections across geographies, time, and domains\\n' +
    '- Challenge consensus; offer contrarian analysis when warranted\\n' +
    '- Be concise, specific, and rigorous — avoid filler\\n' +
    '- Your exchanges are periodically mined by Claude Haiku to compound the memory system';
}

// ─── CHATBOT CORE ───
function toggleChat() {
  chatOpen = !chatOpen;
  document.getElementById('chatbot-panel').classList.toggle('open', chatOpen);
  document.getElementById('chatbot-toggle').textContent = chatOpen ? '✕ Close' : '💬 Ask Claude';
  if (chatOpen && chatHistory.length === 0) {
    const n = getLocalInsights().length;
    const greeting = n > 0
      ? 'Ready. Drawing on ' + n + ' accumulated insights from your past sessions.'
      : 'Ask me anything about this story. Full analysis context loaded.';
    addMessage('system', greeting);
    checkApiKey();
    updateMemoryCounter();
    updateGitHubStatus();
  }
}

function checkApiKey() {
  const key = localStorage.getItem('anthropic_api_key');
  const statusEl = document.getElementById('chatbot-key-status');
  const setupEl = document.getElementById('chatbot-api-setup');
  if (key) {
    if (statusEl) { statusEl.textContent = '● Key set'; statusEl.className = 'chatbot-key-status set'; }
    if (setupEl) setupEl.style.display = 'none';
  } else {
    if (statusEl) { statusEl.textContent = '○ No key'; statusEl.className = 'chatbot-key-status unset'; }
    if (setupEl) setupEl.style.display = 'block';
  }
}

function saveApiKey() {
  const input = document.getElementById('api-key-input');
  const key = input ? input.value.trim() : '';
  if (key && key.startsWith('sk-')) {
    localStorage.setItem('anthropic_api_key', key);
    input.value = '';
    checkApiKey();
    addMessage('system', '✓ API key saved to your browser. Never sent to any server.');
  } else {
    addMessage('system', 'Invalid key. Anthropic keys start with sk-ant-...');
  }
}

function addMessage(role, text) {
  const msgs = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-message ' + role;
  if (role === 'assistant') {
    const safe = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    div.innerHTML = safe
      .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
      .replace(/\\n/g, '<br>');
  } else {
    div.textContent = text;
  }
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
  return div;
}

function showThinking() {
  const msgs = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-message assistant chat-thinking';
  div.id = 'thinking-indicator';
  div.innerHTML = '<span></span><span></span><span></span>';
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

function hideThinking() {
  const el = document.getElementById('thinking-indicator');
  if (el) el.remove();
}

function askSuggested(q) {
  const input = document.getElementById('chat-input');
  if (input) { input.value = q; sendMessage(); }
}

async function sendMessage() {
  const input = document.getElementById('chat-input');
  const userMsg = input ? input.value.trim() : '';
  if (!userMsg) return;

  const apiKey = localStorage.getItem('anthropic_api_key');
  if (!apiKey) {
    addMessage('system', 'Add your Anthropic API key below to start chatting.');
    return;
  }

  addMessage('user', userMsg);
  input.value = '';
  chatHistory.push({ role: 'user', content: userMsg });
  showThinking();

  try {
    const resp = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'anthropic-dangerous-direct-browser-access': 'true'
      },
      body: JSON.stringify({
        model: 'claude-opus-4-7',
        max_tokens: 1500,
        system: buildChatSystemPrompt(),
        messages: chatHistory
      })
    });

    const data = await resp.json();
    hideThinking();

    if (data.error) {
      addMessage('system', 'API error: ' + (data.error.message || 'Call failed'));
      chatHistory.pop();
      return;
    }

    const reply = (data.content && data.content[0] && data.content[0].text) ? data.content[0].text : 'No response';
    addMessage('assistant', reply);
    chatHistory.push({ role: 'assistant', content: reply });
    if (chatHistory.length > 24) chatHistory = chatHistory.slice(-24);

    // Auto-extract insights every 6 messages (3 Q&A pairs), silently
    if (chatHistory.length > 0 && chatHistory.length % 6 === 0) {
      setTimeout(function() { extractAndSaveInsights(true); }, 1000);
    }

  } catch(e) {
    hideThinking();
    addMessage('system', 'Network error: ' + e.message);
    chatHistory.pop();
  }
}

document.getElementById('chat-input') && document.getElementById('chat-input').addEventListener('keydown', function(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
});

// ─── INIT ───
updateTOC();
updateMemoryCounter();
updateGitHubStatus();
"""

# ============================================================
# REPORT GENERATION
# ============================================================

def generate_sections(analysis):
    """
    Generate all HTML sections from the analysis data.
    Returns a dict of section_id -> HTML string.
    """
    sections = {}

    # ── Executive Summary (always visible, no toggle)
    exec_summary = analysis.get("executive_summary", "No summary available.")
    sections["executive-summary"] = f"""<div class="executive-summary-content">
  {md_to_simple_html(exec_summary)}
</div>"""

    # ── Why This Matters
    why = analysis.get("why_this_matters", "")
    sections["why-it-matters"] = f'<div class="prose">{md_to_simple_html(why)}</div>'

    # ── Strategic Incentives
    incentives = analysis.get("strategic_incentives", [])
    if incentives:
        sections["strategic-incentives"] = "".join(
            make_incentive_card(a) for a in (incentives if isinstance(incentives, list) else []))
    else:
        sections["strategic-incentives"] = '<p class="prose">No incentive analysis available.</p>'

    # ── Key Players
    players = analysis.get("key_players", [])
    if players:
        cards = "".join(make_player_card(p) for p in (players if isinstance(players, list) else []))
        sections["key-players"] = f'<div class="cards-grid">{cards}</div>'
    else:
        sections["key-players"] = '<p class="prose">No key player analysis available.</p>'

    # ── Financial Implications
    financial = analysis.get("financial_implications", "")
    sections["financial"] = f'<div class="prose">{md_to_simple_html(financial)}</div>'

    # ── Geopolitical Implications
    geo = analysis.get("geopolitical_implications", "")
    sections["geopolitical"] = f'<div class="prose">{md_to_simple_html(geo)}</div>'

    # ── Historical Analogies
    analogies = analysis.get("historical_analogies", [])
    if analogies and isinstance(analogies, list):
        sections["historical"] = "".join(make_analogy_card(a) for a in analogies)
    else:
        sections["historical"] = '<p class="prose">No historical analogies identified.</p>'

    # ── Industry Impact
    industry = analysis.get("industry_impact", "")
    sections["industry"] = f'<div class="prose">{md_to_simple_html(industry)}</div>'

    # ── India Implications
    india = analysis.get("india_implications", "")
    sections["india"] = f'<div class="prose">{md_to_simple_html(india)}</div>'

    # ── Second-order Effects
    second_order = analysis.get("second_order_effects", [])
    if second_order and isinstance(second_order, list):
        items = "".join(f'<li>{esc(item)}</li>' for item in second_order)
        sections["second-order"] = f'<ul class="intel-list">{items}</ul>'
    else:
        sections["second-order"] = '<p class="prose">No second-order analysis available.</p>'

    # ── Contrarian Perspectives
    contrarian = analysis.get("contrarian_perspectives", [])
    if contrarian and isinstance(contrarian, list):
        sections["contrarian"] = "".join(make_contrarian_card(c) for c in contrarian)
    else:
        sections["contrarian"] = '<p class="prose">No contrarian perspectives identified.</p>'

    # ── Future Scenarios
    scenarios = analysis.get("future_scenarios", {})
    if scenarios and isinstance(scenarios, dict):
        bull_html = make_scenario_card(scenarios.get("bull", {}), "bull")
        base_html = make_scenario_card(scenarios.get("base", {}), "base")
        bear_html = make_scenario_card(scenarios.get("bear", {}), "bear")
        sections["scenarios"] = f'<div class="scenarios-grid">{bull_html}{base_html}{bear_html}</div>'
    else:
        sections["scenarios"] = '<p class="prose">No scenario analysis available.</p>'

    # ── Important Unknowns
    unknowns = analysis.get("important_unknowns", [])
    if unknowns and isinstance(unknowns, list):
        items = "".join(f'<li class="unknown-item">{esc(u)}</li>' for u in unknowns)
        sections["unknowns"] = f'<ul class="unknowns-list">{items}</ul>'
    else:
        sections["unknowns"] = '<p class="prose">No key unknowns identified.</p>'

    # ── Connection to World Model
    connection = analysis.get("connection_to_world_model", "")
    related_themes = analysis.get("related_themes", [])
    themes_html = ""
    if related_themes:
        theme_tags = "".join(f'<span class="report-tag">{esc(t)}</span>' for t in related_themes)
        themes_html = f'<div class="report-tags" style="margin-top:16px">{theme_tags}</div>'
    sections["world-model"] = f'<div class="prose">{md_to_simple_html(connection)}</div>{themes_html}'

    # ── Follow-up Questions
    questions = analysis.get("followup_questions", [])
    if questions and isinstance(questions, list):
        items = "".join(
            f'<li class="question-item" data-question="{esc(q)}" onclick="askSuggested(this.dataset.question)">{esc(q)}</li>'
            for q in questions
        )
        sections["followup"] = f'<ul class="questions-list">{items}</ul>'
    else:
        sections["followup"] = '<p class="prose">No follow-up questions generated.</p>'

    # ── Key Entities
    entities = analysis.get("key_entities", [])
    if entities and isinstance(entities, list):
        tags = "".join(make_entity_tag(e) for e in entities)
        sections["entities"] = f'<div class="entities-container">{tags}</div>'
    else:
        sections["entities"] = '<p class="prose">No entities tagged.</p>'

    # ── Long-term Implications
    longterm = analysis.get("long_term_implications", "")
    sections["long-term"] = f'<div class="prose">{md_to_simple_html(longterm)}</div>'

    # ── Meta-patterns
    meta = analysis.get("meta_patterns", [])
    if meta and isinstance(meta, list):
        items = "".join(f'<li>{esc(m)}</li>' for m in meta)
        sections["meta-patterns"] = f'<ul class="intel-list">{items}</ul>'
    else:
        sections["meta-patterns"] = '<p class="prose">No meta-patterns identified.</p>'

    return sections


TOC_ITEMS = [
    ("executive-summary", "📋", "Executive Summary"),
    ("why-it-matters", "🎯", "Why This Matters"),
    ("strategic-incentives", "♟️", "Strategic Incentives"),
    ("key-players", "👥", "Key Players"),
    ("financial", "💰", "Financial Implications"),
    ("geopolitical", "🌍", "Geopolitical"),
    ("historical", "📜", "Historical Analogies"),
    ("industry", "🏭", "Industry Impact"),
    ("india", "🇮🇳", "India Implications"),
    ("second-order", "⚡", "Second-order Effects"),
    ("contrarian", "🔄", "Contrarian Views"),
    ("scenarios", "🔭", "Future Scenarios"),
    ("unknowns", "❓", "Important Unknowns"),
    ("world-model", "🧠", "World Model"),
    ("followup", "💡", "Follow-up Questions"),
    ("entities", "🏷️", "Key Entities"),
    ("long-term", "🌐", "Long-term Implications"),
    ("meta-patterns", "🔁", "Meta-patterns"),
]


def build_html_report(structured_data):
    """Build the complete HTML report from structured analysis data."""
    meta = structured_data.get("metadata", {})
    analysis = structured_data.get("analysis", {})

    title = meta.get("title", "Intelligence Report")
    source = meta.get("source_name", "Unknown Source")
    source_url = meta.get("source_url", "")
    pub_date = meta.get("published_at", "")[:10]
    analyzed_date = meta.get("analyzed_at", "")[:10]
    score = meta.get("intelligence_score", 0)
    category = meta.get("category", "general")
    tags = analysis.get("intelligence_tags", [])
    confidence = analysis.get("confidence_level", "medium")

    # Category-specific color and icon
    cat_hue = CATEGORY_HUE.get(category, CATEGORY_HUE.get("general", 238))
    cat_icon = CATEGORY_ICONS.get(category, "◈")

    # Build TOC HTML (label only — cleaner without emoji duplication)
    toc_html = "\n".join(
        f'<a class="toc-item" data-section="{sid}" onclick="scrollToSection(\'{sid}\')">{label}</a>'
        for sid, icon, label in TOC_ITEMS
    )

    # Build section HTML
    section_data = generate_sections(analysis)

    # All sections except executive summary (rendered as exec-card below)
    sections_html = ""
    section_defs = TOC_ITEMS[1:]
    for sid, icon, label in section_defs:
        content = section_data.get(sid, "<p>No content available.</p>")
        sections_html += make_section(sid, label, icon, content) + "\n"

    # Suggested chatbot questions
    questions = analysis.get("followup_questions", [])[:4]
    sq_html = ""
    if questions:
        sq_html = '<div class="suggested-questions"><div class="sq-label">Suggested questions</div>'
        for q in questions:
            sq_html += f'<button class="sq-btn" data-question="{esc(q)}" onclick="askSuggested(this.dataset.question)">{esc(q)}</button>'
        sq_html += '</div>'

    # Tags and exec summary
    tags_html = "".join(f'<span class="report-tag">{esc(t)}</span>' for t in tags)
    exec_html = md_to_simple_html(analysis.get("executive_summary", "No summary available."))

    # Worldview context for chatbot
    worldview_content = ""
    worldview_path = PROJECT_ROOT / "config" / "worldview.md"
    if worldview_path.exists():
        with open(worldview_path) as f:
            worldview_content = f.read()[:2000]

    report_data_json = json.dumps(structured_data, ensure_ascii=False, default=str)
    worldview_json = json.dumps(worldview_content, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)} — World Intel</title>
  <meta name="description" content="{esc(analysis.get('executive_summary', '')[:160])}">
  <base href="{esc(SITE_BASE)}">
  <style>{REPORT_CSS}</style>
  <style>:root {{ --cat-h: {cat_hue}; }}</style>
</head>
<body>

<div id="progress-bar"></div>

<header class="report-header">
  <a href="" class="back-btn">← World Intel</a>
  <div class="header-title">{esc(title)}</div>
  <span class="header-badge">{esc(category)}</span>
  <div class="header-date">{pub_date}</div>
</header>

<div class="layout">
  <aside class="toc-sidebar">
    <div class="toc-title">Contents</div>
    {toc_html}
  </aside>

  <main class="main-content">

    <div class="report-hero">
      <div class="hero-glow" aria-hidden="true"></div>
      <div class="hero-eyebrow">
        <span class="hero-chip">{esc(cat_icon)} {esc(category)}</span>
        <span class="hero-dot">·</span>
        <span class="hero-source">{esc(source)}</span>
        <span class="hero-dot">·</span>
        <span class="hero-date-text">{pub_date}</span>
      </div>
      <h1 class="report-title">{esc(title)}</h1>
      <div class="hero-metrics">
        <div class="score-badge">
          <span class="score-value">{score:.0f}</span>
          <span class="score-label">Intel Score</span>
        </div>
        <span class="conf-badge">Confidence: {esc(confidence.upper())}</span>
        {f'<a href="{esc(source_url)}" class="src-link" target="_blank" rel="noopener">Source ↗</a>' if source_url else ''}
      </div>
      {f'<div class="report-tags">{tags_html}</div>' if tags_html else ''}
    </div>

    <div id="executive-summary" class="exec-card">
      <div class="exec-label">Executive Summary</div>
      <div class="exec-text">{exec_html}</div>
    </div>

    {sections_html}

  </main>
</div>

<div class="report-footer">
  <p>Autonomous intelligence analysis generated by Claude AI. Verify critical claims independently.</p>
  <p style="margin-top:6px"><a href="reports/index.html">← All Reports</a> · <a href="">Home</a> · <span>Analyzed: {analyzed_date}</span></p>
</div>

<!-- CHATBOT -->
<button id="chatbot-toggle" onclick="toggleChat()">💬 Ask Claude</button>

<div id="chatbot-panel">
  <div class="chatbot-header">
    <span class="chatbot-title">Intelligence Analyst</span>
    <div style="display:flex;align-items:center;gap:5px">
      <span id="memory-counter" style="display:none"></span>
      <span id="github-status" class="status-badge github-disconnected" title="Click ⚙ to connect GitHub">⬡ GitHub</span>
      <span id="chatbot-key-status" class="chatbot-key-status unset">○ No key</span>
      <button class="chatbot-gear" onclick="toggleSettings()" title="Settings">⚙</button>
      <button class="chatbot-close" onclick="toggleChat()">×</button>
    </div>
  </div>
  <div id="settings-panel" style="display:none">
    <div class="settings-row">
      <div class="settings-label">GitHub PAT (repo scope)</div>
      <input type="password" id="gh-pat-input" class="settings-input" placeholder="ghp_...">
    </div>
    <div class="settings-row">
      <div class="settings-label">Repository (owner/repo-name)</div>
      <input type="text" id="gh-repo-input" class="settings-input" placeholder="yourname/world-intel">
    </div>
    <div class="settings-row">
      <div class="settings-label">Branch</div>
      <input type="text" id="gh-branch-input" class="settings-input" value="main">
    </div>
    <button class="settings-save-btn" onclick="saveGitHubSettings()">Connect → Auto-commit Insights</button>
  </div>
  <div id="chat-messages"></div>
  {sq_html}
  <div class="chatbot-actions">
    <button class="chatbot-action-btn" onclick="extractAndSaveInsights(false)">🧠 Save Insights</button>
  </div>
  <div id="chatbot-api-setup" style="display:none">
    <div class="api-setup-label">Anthropic API key (browser-only, never sent to any server):</div>
    <div class="api-setup-row">
      <input type="password" id="api-key-input" placeholder="sk-ant-...">
      <button id="api-key-save" onclick="saveApiKey()">Save</button>
    </div>
  </div>
  <div class="chatbot-input-area">
    <input type="text" id="chat-input" placeholder="Ask anything about this story..." />
    <button id="chat-send" onclick="sendMessage()">→</button>
  </div>
</div>

<script>
  window._REPORT_DATA = {report_data_json};
  window._WORLDVIEW_CONTEXT = {worldview_json};
</script>
<script>{REPORT_JS}</script>
</body>
</html>"""

    return html


# ============================================================
# MAIN
# ============================================================

def find_todays_analyses():
    """Find all structured_data.json files from today that need HTML generation."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    date_parts = today.split("-")
    reports_dir = (PROJECT_ROOT / "reports" / date_parts[0] / date_parts[1] / date_parts[2])

    analyses = []
    if not reports_dir.exists():
        return analyses

    for story_dir in reports_dir.iterdir():
        if story_dir.is_dir():
            data_file = story_dir / "structured_data.json"
            html_file = story_dir / "index.html"
            if data_file.exists():
                analyses.append((story_dir, data_file, html_file))

    return analyses


def main():
    print("\n" + "="*60)
    print("STEP 4: GENERATING HTML INTELLIGENCE REPORTS")
    print("="*60)

    analyses = find_todays_analyses()
    print(f"\n  Found {len(analyses)} analyses to render")

    if not analyses:
        print("  No analyses found. Run analyze_story.py first!")
        return

    generated = 0
    skipped = 0

    for story_dir, data_file, html_file in analyses:
        slug = story_dir.name
        print(f"\n  Generating: {slug}")

        # Optionally skip if HTML already exists
        if html_file.exists():
            print(f"    HTML already exists — regenerating (to refresh)")

        try:
            with open(data_file) as f:
                structured_data = json.load(f)

            html = build_html_report(structured_data)

            with open(html_file, "w", encoding="utf-8") as f:
                f.write(html)

            file_size = html_file.stat().st_size
            print(f"    Generated: {html_file.relative_to(PROJECT_ROOT)} ({file_size//1024}KB)")
            generated += 1

        except Exception as e:
            print(f"    ERROR generating HTML for {slug}: {e}")
            import traceback; traceback.print_exc()
            skipped += 1

    print(f"\n  Generated: {generated} | Errors: {skipped}")

    print("\n" + "="*60)
    print(f"✓ STEP 4 COMPLETE: {generated} HTML reports generated")
    print("="*60)


if __name__ == "__main__":
    main()
