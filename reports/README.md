# /reports — Intelligence Report Archive

This is the primary intelligence archive. Every story analysis produces a report folder.

## Directory Structure

```
reports/
└── YYYY/          (year)
    └── MM/        (month, zero-padded)
        └── DD/    (day, zero-padded)
            └── story-slug/
                ├── index.html          Beautiful HTML report with chatbot
                ├── structured_data.json Full structured analysis
                ├── summary.md          Brief summary
                ├── raw_analysis.md     Full Claude response
                ├── memory_updates.md   Updates applied to memory
                ├── connections.md      World model connections
                └── followup_questions.md Questions raised
```

## Browsing Reports

- **Web**: Visit the GitHub Pages site → Reports section
- **GitHub**: Browse this folder directly in the GitHub file explorer
- **Local**: Open any `index.html` in your browser

## Archive Properties

- Reports are permanent (never deleted automatically)
- Each report is a complete self-contained HTML file
- Git tracks every report as a versioned artifact
- The archive grows indefinitely without size issues

## Scale Estimation

At 5 stories/day × 365 days/year = ~1,825 reports per year.
This is well within GitHub's storage and performance limits.
Even at 10 years = ~18,250 reports, the repo will be ~5GB (mostly HTML text).

## Searching the Archive

Since everything is markdown/JSON/HTML in GitHub:
- GitHub's code search searches across all reports
- The web interface has category filtering
- `grep -r "search term" reports/` works locally
