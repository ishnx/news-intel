# Architecture Reference
## Technical Deep-Dive

---

## Repository Structure

```
/
├── .github/
│   └── workflows/
│       └── intelligence.yml     # Main automation workflow
│
├── config/                      # ALL system behavior lives here
│   ├── feeds.yaml               # News sources
│   ├── schedules.yaml           # Timing and limits
│   ├── analysis_prompt.md       # Claude's instructions
│   ├── worldview.md             # Strategic priors
│   ├── ranking_rules.md         # How stories are scored
│   ├── intelligence_scoring.md  # Scoring dimensions
│   ├── learning_rules.md        # Memory accumulation rules
│   ├── report_template_rules.md # Report design principles
│   ├── topic_weights.json       # Topic priority weights
│   ├── source_weights.json      # Source trust levels
│   └── entity_priorities.json   # Tracked entities
│
├── memory/                      # Persistent intelligence memory
│   ├── master_memory.md         # Facts and insights
│   ├── active_theses.md         # Strategic beliefs + evidence
│   ├── recurring_patterns.md    # Repeating dynamics
│   ├── unresolved_questions.md  # Open questions
│   ├── worldview_evolution.md   # How understanding changed
│   └── predictions.md           # Scenario prediction tracking
│
├── world_model/                 # Entity knowledge graph
│   ├── companies/               # Company files (auto-generated)
│   ├── countries/               # Country files (auto-generated)
│   ├── people/                  # Person files (auto-generated)
│   ├── technologies/            # Technology files (auto-generated)
│   ├── themes/                  # Theme files (auto-generated)
│   ├── macro/                   # Macro frameworks
│   └── entities/                # General entities
│
├── intelligence/                # Curated collections
│   ├── daily/index.html         # Today's digest
│   ├── weekly/index.html        # Weekly digest
│   └── deep_dives/              # Long-form research
│
├── reports/                     # Intelligence archive
│   └── YYYY/MM/DD/
│       └── story-slug/
│           ├── index.html           # Beautiful HTML report
│           ├── structured_data.json # Machine-readable analysis
│           ├── summary.md           # Brief summary
│           ├── raw_analysis.md      # Full Claude response
│           ├── memory_updates.md    # Updates to apply
│           ├── connections.md       # World model connections
│           └── followup_questions.md
│
├── scripts/                     # Python pipeline
│   ├── run_pipeline.py          # Main orchestrator
│   ├── fetch_news.py            # RSS ingestion
│   ├── rank_news.py             # Intelligence scoring
│   ├── analyze_story.py         # Claude analysis
│   ├── generate_report.py       # HTML generation
│   ├── update_memory.py         # Memory evolution
│   └── build_indexes.py         # Navigation pages
│
├── staging/                     # Intermediate pipeline data
│   ├── raw/YYYY-MM-DD/
│   │   └── articles.json        # Raw fetched articles
│   └── ranked/YYYY-MM-DD/
│       ├── ranked_articles.json # All articles ranked
│       └── top_stories.json     # Top N for analysis
│
├── logs/                        # Pipeline run logs
│   └── YYYY-MM-DD.json          # Per-day run log
│
├── templates/                   # (Reference only)
│   └── report_template.html     # Design reference
│
├── index.html                   # GitHub Pages landing page
├── requirements.txt             # Python dependencies
├── .gitignore                   # Git exclusions
├── README.md                    # User documentation
├── PRD.md                       # Product requirements
├── SETUP_GUIDE.md               # Setup instructions
└── ARCHITECTURE.md              # This file
```

---

## Data Flow

### 1. Ingestion Layer (fetch_news.py)

```
config/feeds.yaml → feedparser → articles.json
```

- Reads feed URLs from `config/feeds.yaml`
- Uses feedparser to parse RSS/Atom feeds
- Handles encoding, dates, HTML stripping
- Deduplicates by URL and title similarity
- Output: `staging/raw/YYYY-MM-DD/articles.json`

**Data format:**
```json
{
  "id": "abc123def456",
  "title": "Article Title",
  "url": "https://...",
  "summary": "Article text...",
  "published_at": "2024-01-01T00:00:00+00:00",
  "source_name": "Source Name",
  "category": "technology",
  "source_weight": 0.9
}
```

### 2. Ranking Layer (rank_news.py)

```
articles.json + config/*.json → ranked_articles.json → top_stories.json
```

- Loads articles from staging
- Applies multi-factor scoring:
  - Source quality (from source_weights.json)
  - Topic relevance (keyword match against topic_weights.json)
  - Entity priority (match against entity_priorities.json)
  - Intelligence keywords (hardcoded high-signal terms)
  - Recency (freshness bonus)
  - Novelty (penalty for similarity to recent analyses)
- Outputs ranked list and top N stories

### 3. Analysis Layer (analyze_story.py)

```
top_stories.json + memory/ + config/ → Claude API → structured_data.json
```

- Loads memory context (worldview, theses, patterns, questions)
- For each story: builds prompt, calls Claude API
- Parses JSON response
- Saves: structured_data.json, summary.md, memory_updates.md, etc.

**Analysis JSON structure:**
```json
{
  "metadata": { "title", "source", "score", "analyzed_at" },
  "analysis": {
    "executive_summary": "...",
    "why_this_matters": "...",
    "strategic_incentives": [{"actor", "incentive", "constraint", "likely_action"}],
    "key_players": [{"name", "role", "position", "power"}],
    "financial_implications": "...",
    "geopolitical_implications": "...",
    "historical_analogies": [{"analogy", "period", "lesson", "where_analogy_breaks"}],
    "industry_impact": "...",
    "india_implications": "...",
    "second_order_effects": ["..."],
    "contrarian_perspectives": [{"view", "reasoning", "confidence"}],
    "future_scenarios": {
      "bull": {"title", "description", "probability", "indicators"},
      "base": {"title", "description", "probability", "indicators"},
      "bear": {"title", "description", "probability", "indicators"}
    },
    "important_unknowns": ["..."],
    "connection_to_world_model": "...",
    "followup_questions": ["..."],
    "key_entities": [{"name", "type", "significance"}],
    "long_term_implications": "...",
    "meta_patterns": ["..."],
    "memory_updates": {
      "new_insights": ["..."],
      "thesis_updates": [{"thesis", "update", "action"}],
      "pattern_updates": [{"pattern", "observation"}],
      "new_questions": ["..."],
      "entity_updates": [{"entity", "update"}]
    }
  }
}
```

### 4. Report Generation (generate_report.py)

```
structured_data.json + config/worldview.md → index.html
```

- Loads structured data
- Generates HTML for each section using Python string formatting
- Embeds the full JSON data as a JavaScript variable
- Embeds worldview context for chatbot
- Writes self-contained HTML file (~100-200KB)

**Report features:**
- All CSS inlined (no external dependencies)
- All JS inlined (no external dependencies)
- Reading progress bar
- Sticky TOC with active highlighting
- Collapsible sections
- Scenario cards (Bull/Base/Bear)
- Entity tags with tooltips
- Embedded chatbot (calls Anthropic API directly from browser)

### 5. Memory Update (update_memory.py)

```
structured_data.json → memory/*.md + world_model/**/*.md
```

- Reads memory_updates from each analyzed story
- Applies updates to persistent memory files:
  - New insights → master_memory.md
  - Thesis updates → active_theses.md
  - Pattern updates → recurring_patterns.md
  - New questions → unresolved_questions.md
  - Entity updates → world_model/[type]/[entity].md
  - Meta patterns → worldview_evolution.md
  - Scenarios → predictions.md (for tracking)

### 6. Index Building (build_indexes.py)

```
reports/**/*.json → index.html, reports/index.html, intelligence/*/index.html
```

- Scans all structured_data.json files
- Generates report cards
- Builds: main index, reports archive, daily digest, weekly digest

---

## Chatbot Architecture

The embedded chatbot is unusual: it calls the Anthropic API **directly from the browser**.

### How It Works

1. User enters their API key in the chatbot panel
2. Key is stored in `localStorage` (browser memory)
3. Key is **never** sent to GitHub or any server
4. When user sends a message, the browser calls `https://api.anthropic.com/v1/messages`
5. The system prompt includes the full report JSON + worldview context
6. Response appears in the chat panel

### Why This Approach

- No backend server needed (stays with GitHub-only philosophy)
- API key is completely private (never leaves the browser)
- Each user uses their own API quota
- Works on any static hosting

### The API Call

```javascript
fetch('https://api.anthropic.com/v1/messages', {
  method: 'POST',
  headers: {
    'x-api-key': apiKey,
    'anthropic-version': '2023-06-01',
    'anthropic-dangerous-direct-browser-access': 'true'
  },
  body: JSON.stringify({
    model: 'claude-opus-4-7',
    max_tokens: 1024,
    system: systemPromptWithFullContext,
    messages: chatHistory
  })
})
```

Note: `anthropic-dangerous-direct-browser-access: true` is required for
browser-side API calls. This header acknowledges that the API key is exposed
in the browser (it's in localStorage, not the HTML source).

---

## GitHub Actions Architecture

### Workflow Triggers

1. **Cron**: Runs on schedule (default: twice daily)
2. **workflow_dispatch**: Manual trigger from Actions tab
3. **Push** (optional, commented out): Runs after config changes

### Permissions

- `contents: write` — for committing outputs
- `pages: write` — for deploying to GitHub Pages
- `id-token: write` — required for OIDC Pages authentication

### Concurrency

```yaml
concurrency:
  group: intelligence-pipeline
  cancel-in-progress: false
```

Only one pipeline runs at a time. If triggered while running, the new run
waits (doesn't cancel the current run). This prevents partial writes to memory.

### Commit Strategy

The pipeline commits with this strategy:
1. `git add reports/ memory/ world_model/ staging/ logs/ index.html`
2. Check `git diff --staged` — if empty, skip commit (idempotent)
3. Build commit message with date and story count
4. `git push` with GITHUB_TOKEN

### Pages Deployment

Uses the official GitHub Pages Actions:
1. `configure-pages` — sets up Pages
2. `upload-pages-artifact` — uploads the entire repo as the site
3. `deploy-pages` — deploys the artifact

The entire repo becomes the website. All HTML files are accessible.

---

## Dependencies

```
anthropic>=0.34.0    # Claude API client
feedparser>=6.0.11   # RSS/Atom parsing
requests>=2.31.0     # HTTP client
PyYAML>=6.0.1        # YAML parsing
python-dateutil>=2.8.2  # Date parsing
beautifulsoup4>=4.12.0  # HTML text extraction (optional but recommended)
markdown>=3.5.0         # Markdown rendering for indexes
```

Total: 6 packages + transitive dependencies.
No database clients, no ORMs, no web frameworks, no frontend tooling.

---

## Scaling Considerations

### Repository Size

Approximate growth rate: ~2MB/day at 5 stories/day
- 1 year: ~730MB
- 5 years: ~3.6GB (approaching GitHub's 5GB soft limit)

Mitigation options:
- Compress HTML (current: ~150KB/report → gzip: ~30KB)
- Archive old staging files (staging files can be deleted after 30 days)
- Use Git LFS for large binary assets (not currently used)

### GitHub Actions Minutes

At 2 runs/day × 15 min/run = 30 min/day = ~900 min/month
GitHub free tier: 2,000 min/month — comfortable headroom.

### API Costs

At 5 stories/day, ~1500 input tokens + ~2000 output tokens per story:
~17,500 tokens/day × $15/Mtok (Opus) = ~$0.26/day = ~$7.80/month

Adjust `stories_per_run` and `max_tokens_per_analysis` to control costs.

---

## Extension Points

### Adding New Report Sections

1. Add the section to the JSON schema in `config/analysis_prompt.md`
2. Add a generation function in `scripts/generate_report.py`
3. Add to the TOC_ITEMS list in `generate_report.py`
4. Add to the section definitions

### Adding New Memory Types

1. Create a new memory file in `memory/`
2. Add loading in `scripts/analyze_story.py` (load_memory_context function)
3. Add updating in `scripts/update_memory.py`

### Adding New Intelligence Sources

Beyond RSS feeds, you could extend `fetch_news.py` to:
- Scrape specific web pages
- Call news APIs (NewsAPI, etc.)
- Monitor Twitter/X (via API)
- Process email newsletters
- Connect to financial data APIs

### Adding Scheduled Deep Dives

Create a second GitHub Actions workflow that runs weekly and:
1. Picks a theme from `memory/active_theses.md`
2. Gathers multiple relevant stories
3. Runs a synthesizing analysis
4. Generates a long-form deep dive report
