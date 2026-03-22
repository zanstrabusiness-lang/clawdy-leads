# Clawdy Leads

Lead discovery and outreach toolkit for local businesses. Clawdy automatically researches prospects, generates free homepage previews, and tracks outreach so Sven can follow up with personalized pitches.

## Lead research automation
- Configure `leads/config.json` with the cities, categories, and query templates you care about.
- Install the Python dependency (`pip install -r requirements.txt`) and export your Brave API token via `BRAVE_API_KEY`.
- Run `python leads/search_leads.py` to cycle through the templated queries, gather the Brave Search results, and save them under `leads/data/`.
- Inspect `leads/data/index.json` for a history of each search plus the generated files containing titles, URLs, and snippets.

## Next steps
- Build a preview homepage generator for each prospect.
- Store contact info and outreach status in `leads/` data files.
- Draft outreach templates that point people to the live preview link.
