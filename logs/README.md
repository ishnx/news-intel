# /logs — Pipeline Run Logs

This folder contains logs from each pipeline run.

## Files

| Pattern | Contents |
|---------|---------|
| `pipeline_YYYY-MM-DD.json` | Run metadata: status, timing, steps completed |
| `memory_update_YYYY-MM-DD.md` | Memory update summaries |

## Format

`pipeline_YYYY-MM-DD.json` contains an array of run records:
```json
[
  {
    "run_at": "2024-01-01T06:00:00+00:00",
    "status": "SUCCESS",
    "elapsed_seconds": 487,
    "steps_run": ["fetch", "rank", "analyze", "report", "memory", "index"],
    "date": "2024-01-01"
  }
]
```

## Purpose

- Debug failed runs
- Track pipeline performance over time
- Audit what was analyzed on any given day

Logs are committed to GitHub as part of the standard pipeline output.
