# Product Requirements Document
## World Intelligence System

**Version:** 1.0
**Philosophy:** GitHub as the database, memory, deployment platform, and learning substrate.

---

## Vision

An autonomous, compounding intelligence system that becomes genuinely smarter
over time — building a deep, interconnected understanding of the world that no
single analyst could maintain manually.

Not a news aggregator. Not a summarizer. A **strategic intelligence organism**.

The key insight: intelligence compounds. The 100th analysis should be dramatically
richer than the 1st because it knows what the 1st through 99th analyses revealed.

---

## Philosophy

### GitHub is Everything

Every piece of information that matters lives in the GitHub repository:
- **Memory** = Markdown files in `memory/`
- **World model** = Markdown files in `world_model/`
- **Intelligence archive** = HTML/JSON/Markdown in `reports/`
- **Configuration** = YAML/JSON/Markdown in `config/`
- **Versioning** = Git history is the audit trail
- **Deployment** = GitHub Pages
- **Automation** = GitHub Actions

This is not a database bypass — it is the correct database for this use case.
Git is a distributed, versioned, human-readable, universally accessible database.

### Transparency is a Core Feature

Every analytical decision must be inspectable and modifiable.
- Ranking algorithm? In `config/intelligence_scoring.md`
- Analysis prompts? In `config/analysis_prompt.md`
- Strategic priors? In `config/worldview.md`
- Memory? In `memory/`

Non-coders should be able to reshape system behavior by editing text files.

### Intelligence Quality Over Volume

5 deeply analyzed stories per day > 50 shallow summaries.
The system is designed to slow down and think deeply, not to "cover" the news.

---

## Core System Architecture

### The Pipeline

```
RSS Feeds → fetch_news.py → [raw articles]
         → rank_news.py → [top N articles]
         → analyze_story.py → [structured analysis JSON]
         → generate_report.py → [HTML reports]
         → update_memory.py → [updated memory files]
         → build_indexes.py → [navigation pages]
         → git commit + push → [GitHub receives everything]
         → GitHub Pages deployment → [public access]
```

### The Memory Loop

The critical design feature is the feedback loop:

1. Analysis runs with current memory as context
2. Analysis produces memory updates
3. Memory updates are applied
4. Next analysis runs with enriched memory
5. Repeat

Over time, this creates genuine compound intelligence.

---

## Memory Architecture

### Five Memory Layers

**Layer 1: Concrete Facts (master_memory.md)**
- Hard, specific, verifiable information
- Example: "TSMC started construction of Arizona fab 2 on 2023-11-14"
- Never expires (can be annotated as outdated)
- Grows monotonically

**Layer 2: Active Theses (active_theses.md)**
- Falsifiable strategic beliefs being tracked
- Each thesis has a conviction level and evidence log
- Gets stronger or weaker with evidence
- Gets closed when resolved

**Layer 3: Recurring Patterns (recurring_patterns.md)**
- Dynamics observed in 2+ situations
- The highest-value long-term learning
- Example: "Regulatory bodies consistently take 18-24 months to regulate new technologies"
- Abstracted from specific instances

**Layer 4: Open Questions (unresolved_questions.md)**
- Genuine knowledge gaps
- Future news is monitored for answers
- Answers move to master_memory.md

**Layer 5: Entity Knowledge (world_model/)**
- Per-entity markdown files
- Accumulate everything known about that entity
- Auto-created when entities first appear

### Memory Context in Analysis

When Claude analyzes a story, it receives:
- Current worldview (from config/worldview.md)
- Active theses (from memory/active_theses.md)
- Recurring patterns (from memory/recurring_patterns.md)
- Open questions (from memory/unresolved_questions.md)
- Recent report summaries (for connection-making)

This context is what enables the compound intelligence property.

---

## Intelligence Report Architecture

### Why 20 Sections?

Each section serves a specific purpose in the intelligence stack:

1. **Executive Summary**: The 30-second answer to "what does this mean?"
2. **Why This Matters**: Forces justification of selection
3. **Strategic Incentives**: Actor-based analysis (game theory)
4. **Key Players**: Named accountability for key actors
5. **Financial Implications**: Capital allocation signals
6. **Geopolitical Implications**: Power relationship changes
7. **Historical Analogies**: Pattern matching to known events
8. **Industry Impact**: Sector-level disruption analysis
9. **India Implications**: India-specific lens (primary geographic focus)
10. **Second-order Effects**: Downstream consequences not obvious from headline
11. **Contrarian Perspectives**: Challenge the consensus
12. **Future Scenarios**: Bull/Base/Bear with probabilities
13. **Important Unknowns**: Honest epistemic humility
14. **Connection to World Model**: Links to accumulated knowledge
15. **Related Reports**: Cross-references in the archive
16. **Follow-up Questions**: Primes future analysis
17. **Key Entities**: Tags for cross-reference
18. **Long-term Implications**: 5-10 year horizon
19. **Meta-patterns**: Connects to pattern library

### The Chatbot

The embedded chatbot serves several functions:
1. Interactive deepening of any section
2. Challenging the analysis
3. Connecting to other reports
4. Generating scenarios not in the main analysis
5. Answering specific questions about the story

Critically: The chatbot has the full report context AND the worldview context.
It's not a generic chatbot — it's a specialized analyst for that specific story.

---

## Ranking System Design

### Why Not Use Popularity?

News ranking by popularity optimizes for:
- Emotional resonance
- Political polarization
- Click-bait quality
- Short-term relevance

We optimize for:
- Long-term strategic significance
- Second-order effects
- Capital allocation implications
- Civilizational importance

A regulatory ruling in Brussels that nobody covered widely might score higher
than a viral tweet from a public figure.

### Scoring Architecture

The score is a weighted combination of:
1. Source quality (is this a trustworthy source?)
2. Topic relevance (does this cover priority topics?)
3. Entity priority (are tracked entities involved?)
4. Intelligence keywords (structural/paradigm-shift signals)
5. Recency (fresh information premium)
6. Novelty (don't re-analyze the same story)

All weights are exposed in config/ files and editable.

---

## Automation Architecture

### GitHub Actions as Orchestrator

GitHub Actions provides:
- Cron scheduling (runs on schedule)
- Secret management (API key never exposed)
- Python runtime (runs the pipeline)
- Git operations (commits outputs)
- Pages deployment (publishes site)

No external services needed. GitHub is the infrastructure.

### The Commit-as-Memory Pattern

After each pipeline run, all outputs are committed to GitHub.
This means:
- Every report is versioned
- Every memory update is versioned
- Every worldview evolution is versioned
- You can `git log` to see the intellectual history of the system
- You can `git diff` to see exactly what changed in each run

### Idempotency

The pipeline is designed to be idempotent — running it twice doesn't
produce duplicate outputs. Each step checks what already exists before
generating new content.

---

## Learning System Design

### What the System Learns

- **Factual knowledge**: Concrete facts extracted from stories
- **Pattern recognition**: Dynamics that repeat across events
- **Thesis evidence**: Which strategic beliefs are holding up
- **Prediction calibration**: Track record of scenario predictions
- **Prompt evolution**: What analytical approaches work best

### What the System Does NOT Learn

- Raw conversation history
- Article text verbatim
- Transient price movements
- Ephemeral sentiment

### Prompt Evolution

The analysis_prompt.md file includes a Prompt Evolution Log.
When the system identifies that a particular analytical approach
consistently produces valuable insights, that approach gets codified
and added to the prompt.

Over time, the prompt itself becomes a distillation of what works.

---

## Scaling Properties

### Storage Scaling

At 5 stories/day:
- Year 1: ~1,825 HTML reports + JSON + Markdown = ~500MB
- Year 5: ~9,125 reports = ~2.5GB
- Year 10: ~18,250 reports = ~5GB

GitHub repos support up to 5GB. Even at maximum scale,
this system fits within free GitHub limits.

### Performance Scaling

- Index page generation: O(n) in number of reports — stays fast
- Memory context: Truncated to configured character limits — stays fast
- Entity files: Individual markdown files — scales to thousands

### Intelligence Scaling

- Each new report adds to memory context
- Memory context is truncated but summarized — signal grows, noise filtered
- Entity files accumulate richer context
- Pattern library grows more predictive

---

## Security Model

### API Key Security

The Anthropic API key is stored only in:
1. GitHub Secrets (for automated runs)
2. Browser localStorage (for chatbot — per user, never committed)

It is NEVER in:
- Code files
- Committed markdown
- HTML reports
- Log files

### Data Sensitivity

All content generated is based on publicly available news.
No private or sensitive information is processed.

Reports are public (deployed to GitHub Pages).
The only secret is the Anthropic API key.

---

## Maintenance Guide

### Daily (Automated)
- ✓ Pipeline runs automatically twice daily
- ✓ Reports generated and committed
- ✓ Memory updated
- ✓ Indexes rebuilt

### Weekly (Manual, Optional)
- Review `memory/active_theses.md` — are the theses still accurate?
- Review `memory/unresolved_questions.md` — any questions answered?
- Review `config/worldview.md` — any views that need updating?
- Check `memory/predictions.md` — any predictions to grade?

### Monthly (Manual, Optional)
- Review `config/feeds.yaml` — are all feeds still active?
- Review `config/entity_priorities.json` — any new entities to track?
- Review `config/topic_weights.json` — any topic priorities to adjust?
- Check GitHub Actions minutes usage (should be well within free limits)

### Debugging

If the pipeline fails:
1. Go to Actions tab → click the failed run
2. Expand each step to see detailed logs
3. Common issues in SETUP_GUIDE.md troubleshooting section

If reports look wrong:
1. Check `staging/ranked/[date]/top_stories.json` — were good stories selected?
2. Check `reports/[date]/[story]/raw_analysis.md` — did Claude respond correctly?
3. Edit `config/analysis_prompt.md` to refine the prompt

---

*This document is itself versioned in Git — its own evolution is tracked.*
