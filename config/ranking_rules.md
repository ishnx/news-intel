# Ranking Rules
## How News Stories Are Prioritized for Analysis

---

## Purpose
This file documents the logic used by `rank_news.py` to score and rank articles.
The top N articles (configured in schedules.yaml) get sent for deep analysis.

---

## The Ranking Pipeline

### Step 1: Source Quality Filter
- Articles from trusted sources (per `source_weights.json`) get a base score boost
- Articles from unknown sources start at a disadvantage
- This prevents spam/PR articles from gaming the system

### Step 2: Topic Relevance Scoring
- Each article is matched against keywords in `topic_weights.json`
- Articles matching high-weight topics (AI, India, semiconductors) rank higher
- Multiple topic matches compound: an AI story about India scores very high

### Step 3: Entity Priority Matching
- Articles mentioning priority-1 entities (per `entity_priorities.json`) get a boost
- This ensures major developments around tracked entities are never missed

### Step 4: Recency Weighting
- Very recent articles (< 6 hours old) get a small freshness boost
- Very old articles (> 20 hours) get slightly deprioritized
- Avoids missing breaking news while not ignoring important slower stories

### Step 5: Novelty Penalty
- Articles that are very similar to already-analyzed recent stories are penalized
- Prevents re-analyzing the same story from 5 different sources
- Uses title similarity (Jaccard coefficient on word overlap)

### Step 6: Intelligence Scoring
- Headline keywords from `intelligence_scoring.md` are applied
- "Breakthrough", "unprecedented", "sanctions" etc. boost scores
- "Report", "analysis", "quarterly earnings" reduce scores (often low novelty)

### Final Score = Base × Source Weight × Topic Weight × Recency × Novelty × Keywords

---

## Anti-Patterns to Avoid
The ranking system explicitly tries to avoid selecting:

1. **Content Marketing**: Company blog posts disguised as news
2. **Wire Repetition**: The same AP/Reuters article reprinted on 10 sites
3. **Predictable Calendar Events**: Quarterly earnings, scheduled speeches (unless surprise)
4. **Opinion Without News**: Think pieces not anchored to a new development
5. **Metrics Without Context**: "X stock rose 3%" without explaining why it matters

---

## Manual Override System
You can force a story to the top of the queue by creating a file:
`staging/priority_override.json`

Format:
```json
{
  "force_analyze": [
    {
      "url": "https://...",
      "title": "Story title",
      "reason": "Why I want this analyzed",
      "source": "manual"
    }
  ]
}
```

The pipeline will add these to the analysis queue on the next run.

---

## Tuning the Ranking
If you're consistently seeing stories you don't want:
1. Lower the weight of that topic in `topic_weights.json`
2. Reduce the trust score of that source in `source_weights.json`

If you're missing stories you want:
1. Add the relevant source to `feeds.yaml`
2. Add keywords to the relevant topic in `topic_weights.json`
3. Add relevant entities to `entity_priorities.json`
