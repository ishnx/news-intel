# /world_model — Entity and Theme Knowledge Graph

This folder contains the system's knowledge about specific entities —
people, companies, countries, technologies, and themes that appear repeatedly
in the intelligence stream.

## Subdirectories

| Folder | Contains |
|--------|---------|
| `entities/` | General entities that don't fit other categories |
| `themes/` | Cross-cutting themes (e.g., "AI Arms Race", "Supply Chain Resilience") |
| `countries/` | Country-level strategic intelligence |
| `companies/` | Company-level intelligence |
| `technologies/` | Technology-level intelligence |
| `macro/` | Macroeconomic frameworks and data |
| `people/` | Key individual profiles |

## How Entity Files Work

Each entity gets a markdown file named after it (e.g., `nvidia.md`, `china.md`).
The file contains:
- Overview and current status
- Timeline of developments (most recent at bottom)
- Connections to other entities
- Open questions

## Auto-Generation

The `update_memory.py` script automatically:
- Creates new entity files when new entities appear in analyses
- Appends new developments to existing entity files
- References the source story for each update

## Manual Enrichment

You can enrich entity files manually:
- Add context that news doesn't capture
- Add historical background
- Link related entities
- Mark entities as less/more important

## Growth Pattern

The world model starts sparse and fills in over time.
After 100 analysis runs: ~50-100 entity files
After 500 runs: ~300-500 entity files, rich cross-references
After 1000 runs: A meaningful knowledge graph
