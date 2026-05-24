# Learning Rules
## How the System Evolves and Improves Over Time

---

## Philosophy
This system is not a static tool. It is designed to get smarter with every run.
Each analysis adds to a growing intelligence substrate. Future analyses are
informed by everything that came before.

---

## What Gets Learned

### Level 1: New Facts (Stored in master_memory.md)
Hard, specific information that is unlikely to change:
- "Company X acquired Company Y for $Z billion on [date]"
- "Country A imposed sanctions on Country B covering [sectors]"
- "Technology X demonstrated capability Y for the first time"

These are permanent additions to the knowledge base.

### Level 2: Evolving Theses (Stored in active_theses.md)
Strategic beliefs that get stronger or weaker with evidence:
- "AI will displace X% of white-collar jobs within Y years" — tracking evidence
- "India will attract $X billion in chip manufacturing investment" — tracking evidence

Each analysis that confirms or challenges a thesis updates its confidence level.

### Level 3: Recurring Patterns (Stored in recurring_patterns.md)
Dynamics that repeat across contexts:
- "Technology companies consistently underestimate regulatory response"
- "Geopolitical tensions correlate with supply chain diversification spending"

Patterns are extracted and named when they appear 2+ times.

### Level 4: Unresolved Questions (Stored in unresolved_questions.md)
Genuine unknowns that future news may answer:
- "Will China retaliate against US chip restrictions through rare earth controls?"
- "At what AI capability level does labor displacement become economically visible?"

These prime the system to notice when answers appear in future news.

### Level 5: Entity Relationships (Stored in world_model/)
Evolving understanding of specific entities:
- Who leads them, what their goals are, what constraints they face
- Recent developments, shifts in position
- Relationships with other entities

---

## Memory Update Rules

### What DOES get added to memory:
- Concrete new facts with specific details (dates, numbers, names)
- Thesis confirmations or challenges backed by evidence
- New patterns with at least one clear example
- Questions that future news could plausibly answer
- Significant entity status changes (leadership, strategy, position)

### What does NOT get added to memory:
- Raw article content or quotes (too verbose, becomes noise)
- Opinions without evidence
- Obvious facts already in worldview
- Minute-by-minute price movements
- Speculative predictions without grounding

### Memory Pruning Rules:
- Outdated facts (clearly superseded by newer facts) should be removed
- Resolved questions move from unresolved_questions.md to master_memory.md
- Closed theses move to an "archived theses" section

---

## Prompt Evolution Rules

### When to Update analysis_prompt.md:
The system can add to the "Prompt Evolution Log" in analysis_prompt.md when:
1. A new analytical approach consistently produces better insights
2. A blind spot is repeatedly identified that the prompt doesn't address
3. A new geopolitical or technological reality makes old guidance stale

### Rule: Prompts only get MORE specific, never vaguer
Each prompt update should make the analysis more precise, not less.
Bad update: "Also consider cultural factors"
Good update: "For India stories, explicitly analyze: Tier-1 vs Tier-2 city dynamics,
English-language market vs Hindi-language market, formal vs informal economy"

---

## How the System Measures Its Own Quality

### Prediction Tracking
When the system makes a prediction in a future_scenarios section,
`update_memory.py` logs it in `memory/predictions.md` with:
- The prediction
- The confidence level
- The source story
- A date for review

When evidence arrives, the system updates whether the prediction was correct.
Over time, this builds a track record and can adjust confidence calibration.

### Pattern Validation
When a recurring pattern is flagged, it gets added with a count of 1.
Each new instance increments the count.
Patterns with count > 3 are considered "established" and weighted more heavily.

### Thesis Resolution
When a thesis is confirmed, weakened, or made obsolete by evidence,
the resolution is logged with the confirming/disconfirming story reference.
