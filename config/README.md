# /config — System Configuration

This folder contains ALL configurable behaviors of the intelligence system.
Everything here is designed to be edited by a non-technical user.

## Files In This Folder

| File | What It Controls | Edit To... |
|------|-----------------|------------|
| `feeds.yaml` | News sources | Add/remove news feeds |
| `schedules.yaml` | When system runs | Change run frequency |
| `analysis_prompt.md` | How AI analyzes stories | Change analytical depth/style |
| `worldview.md` | AI's operating beliefs | Shape the analytical perspective |
| `ranking_rules.md` | How stories are prioritized | Understand the ranking system |
| `intelligence_scoring.md` | What makes a story important | Adjust strategic priorities |
| `learning_rules.md` | How system learns over time | Adjust memory accumulation |
| `report_template_rules.md` | How reports look | Change visual design |
| `topic_weights.json` | Topic priorities | Emphasize/de-emphasize topics |
| `source_weights.json` | Source trust levels | Adjust source quality ratings |
| `entity_priorities.json` | Tracked entities | Add people/companies to watch |

## Most Important Files to Customize

### For changing WHAT gets analyzed:
→ Edit `feeds.yaml` (add your favorite news sources)
→ Edit `topic_weights.json` (boost topics you care about)
→ Edit `entity_priorities.json` (add entities you track)

### For changing HOW things are analyzed:
→ Edit `worldview.md` (add your own analytical priors)
→ Edit `analysis_prompt.md` (reshape the AI's reasoning approach)

### For changing WHEN it runs:
→ Edit `schedules.yaml` (change the cron schedule)

## Scaling Philosophy
This folder grows in sophistication over time. As the system analyzes more stories,
the `analysis_prompt.md` file gains a history of what worked. The `worldview.md`
gets updated with refined understanding. Configuration becomes intelligence.
