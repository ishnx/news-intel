# /intelligence — Curated Intelligence Collections

This folder contains curated collections of intelligence organized by time period.

## Subfolders

| Folder | Contains |
|--------|---------|
| `daily/` | Daily intelligence digests (today's top stories) |
| `weekly/` | Weekly synthesis (7-day perspective) |
| `deep_dives/` | Deep research on specific topics |

## How These Are Generated

`build_indexes.py` generates `index.html` in each folder automatically.

- **Daily**: Shows today's analyzed stories
- **Weekly**: Shows the past 7 days of stories  
- **Deep dives**: Manually triggered analysis on specific topics

## Deep Dives

Deep dives are longer-form analyses triggered manually. To request one:
1. Create a `priority_override.json` file in `staging/`
2. Add the topic or specific articles you want analyzed deeply
3. Trigger a manual GitHub Actions run

## Accessing

All content is deployed to GitHub Pages and accessible via:
- `https://[username].github.io/[repo]/intelligence/daily/`
- `https://[username].github.io/[repo]/intelligence/weekly/`
