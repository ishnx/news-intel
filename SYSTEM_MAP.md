# System Map — World Intelligence System

End-to-end flow of every component, file, and data transformation.

---

## The One-Sentence Version

GitHub Actions runs twice a day → Python fetches news → Claude analyzes the top stories → beautiful HTML reports are generated → everything is committed back to GitHub → GitHub Pages serves the site → the next run is smarter because it reads what was written.

---

## Data Flow Diagram

```
                         ┌─────────────────────────────────┐
                         │       GITHUB ACTIONS             │
                         │  (cron: 0 6,18 * * * — UTC)      │
                         └───────────────┬─────────────────┘
                                         │ triggers
                                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   run_pipeline.py                           │
│   Orchestrates all 6 steps in sequence                      │
└──────┬──────────────────────────────────────────────────────┘
       │
       ▼ STEP 1
┌─────────────────┐      reads      ┌───────────────────────┐
│ fetch_news.py   │ ─────────────── │ config/feeds.yaml     │
│                 │                 │ (60+ RSS feed URLs)   │
│ - Parses RSS    │      reads      └───────────────────────┘
│ - Deduplicates  │ ─────────────── ┌───────────────────────┐
│ - Filters old   │                 │ config/schedules.yaml │
└────────┬────────┘                 │ (fetch_window_hours)  │
         │ writes                   └───────────────────────┘
         ▼
┌────────────────────────────────────┐
│ staging/raw/YYYY-MM-DD/            │
│   articles.json                    │
│   (all fetched articles, ~50-200)  │
└────────┬───────────────────────────┘
         │
         ▼ STEP 2
┌─────────────────┐      reads      ┌───────────────────────┐
│ rank_news.py    │ ─────────────── │ config/topic_weights  │
│                 │                 │   .json               │
│ - Scores each   │      reads      └───────────────────────┘
│   article on 5  │ ─────────────── ┌───────────────────────┐
│   dimensions    │                 │ config/entity_        │
│ - Picks top N   │                 │   priorities.json     │
└────────┬────────┘                 └───────────────────────┘
         │ writes
         ▼
┌────────────────────────────────────┐
│ staging/ranked/YYYY-MM-DD/         │
│   ranked_articles.json             │
│   top_stories.json (top 5)         │
└────────┬───────────────────────────┘
         │
         ▼ STEP 3
┌─────────────────┐      reads      ┌───────────────────────┐
│ analyze_story.py│ ─────────────── │ config/analysis_      │
│                 │                 │   prompt.md           │
│ - Loads memory  │      reads      └───────────────────────┘
│   context       │ ─────────────── ┌───────────────────────┐
│ - Calls Claude  │                 │ memory/ files         │
│   API           │                 │ (worldview, theses,   │
│ - Parses JSON   │                 │  patterns, questions) │
│   response      │                 └───────────────────────┘
└────────┬────────┘
         │ writes
         ▼
┌────────────────────────────────────┐
│ reports/YYYY/MM/DD/<slug>/         │
│   structured_data.json ← CORE     │
│   raw_analysis.md                  │
│   summary.md                       │
│   memory_updates.md                │
│   connections.md                   │
│   followup_questions.md            │
└────────┬───────────────────────────┘
         │
         ▼ STEP 4
┌─────────────────┐
│generate_report.py│
│                 │
│ - Reads JSON    │
│ - Renders 20    │
│   sections      │
│ - Embeds chatbot│
│ - Writes HTML   │
└────────┬────────┘
         │ writes
         ▼
┌────────────────────────────────────┐
│ reports/YYYY/MM/DD/<slug>/         │
│   index.html ← THE REPORT         │
│   (self-contained, ~150KB)         │
└────────┬───────────────────────────┘
         │
         ▼ STEP 5
┌─────────────────┐
│update_memory.py │
│                 │
│ - Reads each    │
│   structured_   │
│   data.json     │
│ - Appends to    │
│   memory files  │
│ - Updates world │
│   model entities│
└────────┬────────┘
         │ writes
         ▼
┌────────────────────────────────────┐
│ memory/                            │
│   master_memory.md  ← facts        │
│   active_theses.md  ← beliefs      │
│   recurring_patterns.md ← trends   │
│   unresolved_questions.md          │
│   worldview_evolution.md           │
│   predictions.md                   │
│                                    │
│ world_model/                       │
│   people/<name>.md                 │
│   companies/<name>.md              │
│   countries/<name>.md              │
│   technologies/<name>.md           │
└────────┬───────────────────────────┘
         │
         ▼ STEP 6
┌─────────────────┐
│build_indexes.py │
│                 │
│ - Scans all     │
│   reports/      │
│ - Builds nav    │
│   pages         │
└────────┬────────┘
         │ writes
         ▼
┌────────────────────────────────────┐
│ index.html          ← homepage     │
│ reports/index.html  ← all reports  │
│ intelligence/daily/ ← daily digest │
│ intelligence/weekly/← weekly brief │
└────────┬───────────────────────────┘
         │
         ▼ GitHub Actions commit + Pages deploy
┌────────────────────────────────────┐
│ github.com/you/repo  (git history) │
│ yourname.github.io   (live site)   │
└────────────────────────────────────┘
```

---

## The Compounding Memory Loop

This is the core intelligence engine. Each run reads the memory it wrote last time:

```
Run 1:  analyze(story) → write(memory)          [shallow context]
Run 10: read(memory) → analyze(story) → write(memory)   [richer]
Run 50: read(memory) → analyze(story) → write(memory)   [deep]
Run 100: (noticeably deeper analysis than run 1)
```

**Memory files read by `analyze_story.py` before each analysis:**
- `memory/worldview_evolution.md` — how the system's understanding has evolved
- `memory/active_theses.md` — current high-conviction beliefs to test
- `memory/recurring_patterns.md` — patterns seen repeatedly across stories
- `memory/unresolved_questions.md` — open questions to keep probing

**Memory files written by `update_memory.py` after each analysis:**
- `memory/master_memory.md` — new facts
- `memory/active_theses.md` — thesis updates (strengthen/weaken/close/new)
- `memory/recurring_patterns.md` — pattern observations
- `memory/unresolved_questions.md` — new open questions
- `world_model/[type]/[name].md` — entity-level knowledge

---

## Chatbot Memory Loop (in-browser)

Each report has an embedded chatbot. When you chat:

```
1. You ask a question
2. Claude Opus answers with report + worldview + accumulated insights as context
3. Every 3 exchanges (or manually), Claude Haiku extracts structured insights
4. Insights saved to localStorage (immediate, cross-session persistence)
5. If GitHub PAT configured → auto-committed to memory/master_memory.md
6. Next chat opens with those insights already in the system prompt
```

Storage:
- `localStorage['intel_insights']` — JSON array of up to 200 insights
- `localStorage['intel_settings']` — GitHub PAT, repo, branch
- `localStorage['anthropic_api_key']` — Anthropic key

---

## Directory Structure

```
/
├── .github/workflows/
│   └── intelligence.yml      ← The automation (GitHub Actions)
│
├── config/
│   ├── feeds.yaml            ← RSS feeds (edit to add sources)
│   ├── schedules.yaml        ← Run frequency, story count
│   ├── analysis_prompt.md    ← The analyst persona + output schema
│   ├── topic_weights.json    ← Score boost per topic keyword
│   └── entity_priorities.json← Priority entities to track
│
├── scripts/
│   ├── run_pipeline.py       ← Orchestrator (runs all 6 steps)
│   ├── fetch_news.py         ← Step 1: RSS ingestion
│   ├── rank_news.py          ← Step 2: Intelligence scoring
│   ├── analyze_story.py      ← Step 3: Claude API analysis
│   ├── generate_report.py    ← Step 4: HTML report generation
│   ├── update_memory.py      ← Step 5: Memory accumulation
│   └── build_indexes.py      ← Step 6: Navigation pages
│
├── memory/                   ← Persistent intelligence memory
│   ├── master_memory.md      ← Accumulated facts
│   ├── active_theses.md      ← Tracked beliefs
│   ├── recurring_patterns.md ← Observed patterns
│   ├── unresolved_questions.md
│   ├── worldview_evolution.md
│   └── predictions.md
│
├── world_model/              ← Entity knowledge base
│   ├── people/
│   ├── companies/
│   ├── countries/
│   ├── technologies/
│   └── themes/
│
├── reports/                  ← Generated intelligence reports
│   └── YYYY/MM/DD/<slug>/
│       ├── index.html        ← The report (with chatbot)
│       ├── structured_data.json
│       ├── raw_analysis.md
│       ├── summary.md
│       └── memory_updates.md
│
├── staging/                  ← Intermediate pipeline data
│   ├── raw/YYYY-MM-DD/articles.json
│   └── ranked/YYYY-MM-DD/top_stories.json
│
├── logs/                     ← Run logs
├── index.html                ← Homepage (auto-generated)
├── requirements.txt
└── .nojekyll                 ← Prevents GitHub Pages Jekyll processing
```

---

## Key Secrets and Where They Live

| Secret | Where stored | Never in |
|--------|-------------|---------|
| `ANTHROPIC_API_KEY` | GitHub → Settings → Secrets | Code, commits, HTML |
| Anthropic key (chatbot) | Browser `localStorage` | GitHub, any server |
| GitHub PAT (chatbot memory) | Browser `localStorage` | GitHub, any server |

---

## Configuration Files You Can Edit Without Code

| File | What it controls |
|------|-----------------|
| `config/feeds.yaml` | Which news sources to monitor |
| `config/schedules.yaml` | How often to run, how many stories |
| `config/analysis_prompt.md` | The analyst's persona and focus areas |
| `config/topic_weights.json` | Which topics score higher |
| `config/entity_priorities.json` | Which people/companies to prioritize |
| `memory/active_theses.md` | Pre-seed with your own beliefs to test |
