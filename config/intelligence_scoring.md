# Intelligence Scoring Rules

## What This File Does
This file defines how the system scores every news article to decide which ones
deserve deep analysis. The system reads these rules and applies them automatically.

## Core Philosophy
We do NOT optimize for clicks, shares, or popularity.
We optimize for **strategic intelligence value** — the degree to which a story
will matter for understanding the world 6 months, 2 years, or 10 years from now.

---

## Scoring Dimensions (0-10 each)

### 1. Structural Significance (weight: 2.0)
Does this story represent a **structural change** rather than a cyclical event?
- Structural: New technology paradigm, regulatory framework, geopolitical realignment
- Cyclical: Quarterly earnings, temporary price movements, routine elections
- Score 8-10: Creates new permanent reality
- Score 5-7: Accelerates existing trends  
- Score 0-4: Temporary fluctuation, noise

### 2. Second-Order Effects (weight: 1.8)
How many domains does this story affect beyond the obvious?
- Score 8-10: Ripples across 4+ domains (tech, policy, geopolitics, capital)
- Score 5-7: Affects 2-3 domains
- Score 0-4: Self-contained in one domain

### 3. Capital Flow Implications (weight: 1.5)
Does this story signal where large amounts of money will move?
- Score 8-10: Redirects hundreds of billions in investment
- Score 5-7: Shifts competitive dynamics in a sector
- Score 0-4: Minor capital allocation signal

### 4. Geopolitical Weight (weight: 1.5)
Does this story affect relationships between major powers?
- Score 8-10: US-China, India-US, NATO dynamics
- Score 5-7: Regional power shifts
- Score 0-4: Bilateral minor-country story

### 5. Technology Inflection (weight: 1.7)
Does this story represent a technology crossing a threshold?
- Score 8-10: New capability emerges (AI reasoning, biotech breakthrough)
- Score 5-7: Meaningful progress but incremental
- Score 0-4: Minor product update, feature release

### 6. India Relevance (weight: 1.4)
How directly does this affect India's trajectory?
- Score 8-10: Direct impact on India's economy, policy, or strategic position
- Score 5-7: Indirect but material effect
- Score 0-4: Minimal India connection

### 7. Contrarian Signal (weight: 1.3)
Does the mainstream narrative miss something important about this story?
- Score 8-10: High conviction that consensus view is significantly wrong
- Score 5-7: Some non-consensus elements worth exploring
- Score 0-4: Story is well-covered, consensus seems right

### 8. Urgency / Time Sensitivity (weight: 1.0)
How much does acting on this intelligence SOON matter?
- Score 8-10: Window to act closes within days/weeks
- Score 5-7: 1-6 month horizon
- Score 0-4: Long-term structural, no near-term action

### 9. Historical Novelty (weight: 1.2)
Has anything like this happened before?
- Score 8-10: Genuinely unprecedented
- Score 5-7: Loosely analogous to past events
- Score 0-4: Very similar to well-documented historical events

---

## Keyword Boosters
Certain keywords automatically add +1 to the total score:

**+2 boost keywords (very high strategic value):**
- "AGI", "artificial general intelligence"
- "nuclear", "fusion"
- "Taiwan", "invasion", "war"
- "default", "sovereign debt crisis"
- "pandemic", "pathogen"

**+1 boost keywords (high strategic value):**
- "breakthrough", "paradigm shift", "unprecedented"
- "sanctions", "export controls", "ban"
- "acquisition", "merger" (>$10B)
- "regulation", "law passed", "banned"
- "India", "China", "US", "Russia" (in same headline)

---

## Scoring Formula
```
total_score = sum(dimension_score * dimension_weight) / sum(all_weights)
normalized_score = total_score * 10  # Normalize to 0-100 scale
final_score = normalized_score + keyword_boosts
```

## Minimum Score to Qualify for Analysis
- Full deep analysis: score >= 60
- Brief analysis: score >= 40
- Skip entirely: score < 40

---

## What We Explicitly Deprioritize
- Celebrity/sports news (unless geopolitically relevant)
- Day-trading signals (too short-term)
- Routine product launches (unless paradigm-shifting)
- Press releases disguised as news
- Recycled analysis without new data
- Stories covered identically by 10+ sources (signal extracted, diminishing returns)
