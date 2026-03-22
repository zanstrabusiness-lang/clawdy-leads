# Lead research scripts

These helper files turn Brave Search into a basic local-business lead engine.

## Requirements
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Supply a Brave Search API token via `BRAVE_API_KEY` (preferred) or `--token`. The script sends it in the `X-Subscription-Token` header just like Brave's quickstart sample: `curl "https://api.search.brave.com/res/v1/web/search?q=artificial+intelligence" -H "X-Subscription-Token: YOUR_API_KEY"` ([documentation](https://api-dashboard.search.brave.com/documentation/quickstart)).

## Customize
`leads/config.json` controls the search plan:
- `city`, `categories`, and `query_templates` generate the queries you run.
- `extra_queries` adds bespoke prompts.
- `results_per_query`, `max_queries`, and `delay_seconds` regulate throughput.
- `output_dir` and `metadata_fields` specify where and how we persist results.

Edit that file before you run the script so it targets the niches you care about.

## Run it
```bash
python leads/search_leads.py --config leads/config.json
```
The script:
1. Builds a plan of templated queries (per category + city).
2. Hits Brave's `https://api.search.brave.com/res/v1/web/search` endpoint for each query.
3. Saves each run to `leads/data/` and appends a lightweight index (`index.json`).

## Review results
- `leads/data/index.json` summarizes every query run (timestamp, hit count, file).
- Individual JSON files under `leads/data/` hold the hits (title, URL, snippet) plus the raw payload.

Drop new categories or cities into the config whenever you want to target a fresh niche.
