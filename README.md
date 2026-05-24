# World Intelligence System

> An autonomous, compounding intelligence organism that continuously builds deep understanding of the world.

[![Intelligence Pipeline](https://github.com/Black98Hat/news-intel/actions/workflows/intelligence.yml/badge.svg)](https://github.com/Black98Hat/news-intel/actions/workflows/intelligence.yml)

---

## What This Is

This is not a news app. This is an **autonomous evolving intelligence system** that:

- 🔄 **Autonomously fetches** world/startup/business/geopolitical/technology/economic news
- 🧠 **Deeply analyzes** selected stories using Claude AI
- 📊 **Generates elegant** interactive HTML intelligence reports
- 💾 **Continuously accumulates** memory and worldview over time
- 🌐 **Deploys automatically** to GitHub Pages
- 📈 **Compounds knowledge** — each analysis is richer than the last

**GitHub itself is the database.** No backend needed. No database needed. No cloud infrastructure needed.

---

## Live Site

**→ [View Intelligence Reports](https://Black98Hat.github.io/news-intel/)**

---

## Quick Start (5 Minutes to First Report)

1. **Fork this repository** (button at top right on GitHub)
2. **Add your API key:**
   - Go to Settings → Secrets and Variables → Actions
   - Add secret: `ANTHROPIC_API_KEY` = your Anthropic API key
3. **Enable GitHub Pages:**
   - Go to Settings → Pages → Source: GitHub Actions
4. **Run the pipeline:**
   - Go to Actions → Intelligence Pipeline → Run workflow
5. **View your reports:**
   - Your GitHub Pages site will show the first reports in ~5-10 minutes

Full instructions: [SETUP_GUIDE.md](SETUP_GUIDE.md)

---

## Architecture

```
GitHub Repo
├── 📰 config/feeds.yaml          → News sources (add your feeds)
├── 🧠 config/analysis_prompt.md  → How Claude analyzes stories
├── 🌍 config/worldview.md        → Your strategic priors
├── ⚖️  config/topic_weights.json  → Topic priorities
├── 💾 memory/                    → Accumulating intelligence
│   ├── master_memory.md          → Facts and insights
│   ├── active_theses.md          → Strategic beliefs
│   ├── recurring_patterns.md     → Repeating dynamics
│   └── unresolved_questions.md   → Open questions
├── 🗺️  world_model/               → Entity knowledge graph
│   ├── companies/                → Company intelligence
│   ├── countries/                → Country intelligence
│   ├── people/                   → Key individual profiles
│   └── technologies/             → Technology intelligence
├── 📋 reports/YYYY/MM/DD/slug/   → HTML intelligence reports
├── 🤖 scripts/                   → Python pipeline
└── ⚙️  .github/workflows/         → Automation (runs on schedule)
```

---

## How It Compounds

**Run 1:** System has no memory. Analysis uses only the current worldview config.

**Run 10:** System has analyzed 50 stories. Memory file has concrete facts. Analysis makes connections between current stories and past insights.

**Run 100:** Strong pattern library. Active thesis tracking with evidence log. Entity knowledge files for 50+ tracked entities. Analysis is noticeably richer.

**Run 1000:** Deep institutional knowledge. Predictions tracked and calibrated. A genuine intelligence asset that took years to build but lives in a GitHub repo.

---

## Customization

Everything is configurable by editing plain text files:

| Want to... | Edit this file |
|-----------|---------------|
| Add news sources | `config/feeds.yaml` |
| Change analysis style | `config/analysis_prompt.md` |
| Add strategic priors | `config/worldview.md` |
| Focus on different topics | `config/topic_weights.json` |
| Track new entities | `config/entity_priorities.json` |
| Change run schedule | `config/schedules.yaml` |

---

## Intelligence Report Features

Each generated HTML report includes:
- Executive Summary
- Why This Matters  
- Strategic Incentives (actor by actor)
- Key Players
- Financial Implications
- Geopolitical Implications
- Historical Analogies
- Industry Impact
- India Implications
- Second-order Effects
- Contrarian Perspectives
- Bull/Base/Bear Future Scenarios
- Important Unknowns
- Connection to World Model
- Follow-up Questions
- Key Entities (tagged)
- Long-term Implications
- Meta-patterns
- **Embedded AI chatbot** for interactive deepening

---

## Philosophy

> "The goal is not to read more news. The goal is to understand the world better."

This system optimizes for:
- **Depth** over breadth
- **Strategic significance** over popularity
- **Compounding intelligence** over ephemeral summaries
- **Transparency** — every prompt, rule, and memory is visible and editable
- **Autonomy** — runs itself, updates itself, improves itself

---

## Tech Stack

- **Python 3.11** — pipeline scripts
- **Claude API (Anthropic)** — intelligence analysis
- **feedparser** — RSS/Atom feed ingestion
- **Static HTML/CSS/JS** — reports and interface
- **GitHub Actions** — automation and scheduling
- **GitHub Pages** — deployment
- **Markdown/JSON** — all storage (GitHub is the database)

No React. No backend. No database. No cloud infrastructure beyond GitHub.

---

## Documentation

- [SETUP_GUIDE.md](SETUP_GUIDE.md) — Step-by-step setup (zero coding knowledge required)
- [PRD.md](PRD.md) — Full product requirements and philosophy
- [ARCHITECTURE.md](ARCHITECTURE.md) — Technical architecture deep-dive

---

## License

MIT — use freely, contribute back.

---

*Built with Claude AI + GitHub Actions. Replace `YOUR_USERNAME/YOUR_REPO` with your actual GitHub details.*
