# /memory — Persistent Intelligence Memory

This folder is the system's brain.
Everything the system learns is stored here and fed back into future analyses.

## Memory Files

| File | Purpose | Updated By |
|------|---------|------------|
| `master_memory.md` | Raw facts and insights | Automatically after each run |
| `active_theses.md` | Strategic beliefs being tracked | Automatically after each run |
| `recurring_patterns.md` | Dynamics that repeat across events | Automatically after each run |
| `unresolved_questions.md` | Open questions awaiting resolution | Automatically after each run |
| `worldview_evolution.md` | How understanding has changed over time | Automatically after each run |
| `predictions.md` | Scenario predictions for tracking accuracy | Automatically after each run |

## Memory Philosophy

**What gets stored:**
- Concrete, specific facts (dates, numbers, names)
- Evolving beliefs backed by evidence
- Recurring dynamics observed 2+ times
- Genuine knowledge gaps that future news could fill
- Significant entity status changes

**What does NOT get stored:**
- Raw article text (too verbose)
- Unsupported opinions
- Facts already obvious from the worldview config
- Short-term price movements

## How Memory Compounds

Each analysis run:
1. Reads the current memory state (feeds it to Claude as context)
2. Produces new insights, thesis updates, pattern observations
3. Writes updates back to memory files
4. Future analyses have richer context → produce deeper analysis

After 50 runs: basic pattern library established
After 200 runs: strong thesis tracking, rich entity knowledge
After 1000 runs: deep understanding of evolving global dynamics

## Editing Memory

You can and should edit these files manually!
Add your own insights, modify thesis confidence levels, close resolved questions.
The system treats your edits exactly like its own — they feed into future analyses.

## Scaling

These markdown files can grow to thousands of entries without performance issues.
Git itself versions every change, so nothing is ever lost.
