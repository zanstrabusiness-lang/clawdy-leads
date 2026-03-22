#!/usr/bin/env python3
"""Fetch lead ideas by querying Brave Search with templated prompts."""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set

import requests

API_URL = "https://api.search.brave.com/res/v1/web/search"


class BraveLeadFinder:
    def __init__(self, api_key: str, config: Dict[str, Any]) -> None:
        self.api_key = api_key
        self.config = config
        self.output_dir = Path(config.get("output_dir", "leads/data"))
        if not self.output_dir.is_absolute():
            self.output_dir = Path.cwd() / self.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.output_dir / "index.json"
        self.results_per_query = config.get("results_per_query", 5)
        self.delay_seconds = config.get("delay_seconds", 0)
        self.metadata_fields = config.get(
            "metadata_fields", ["title", "url", "description", "snippet"]
        )
        self.max_queries = config.get("max_queries", 0)

    def search(self, plan: Dict[str, str]) -> Dict[str, Any]:
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }
        params = {
            "q": plan["query"],
            "limit": self.results_per_query,
            "offset": 0,
        }

        response = requests.get(API_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        hits = payload.get("web", {}).get("results", [])
        normalized = self._normalize_hits(hits)
        timestamp = datetime.now(timezone.utc).isoformat()

        return {
            "query": plan["query"],
            "category": plan.get("category"),
            "template": plan.get("template"),
            "timestamp": timestamp,
            "results": normalized,
            "raw": payload,
        }

    def _normalize_hits(self, hits: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for index, hit in enumerate(hits, start=1):
            entry: Dict[str, Any] = {
                "position": index,
            }
            for field in self.metadata_fields:
                entry[field] = hit.get(field)
            normalized.append(entry)
        return normalized

    def persist(self, plan: Dict[str, str], record: Dict[str, Any]) -> Path:
        slug_source = plan["query"]
        slug = slugify(slug_source)
        now = datetime.now(timezone.utc)
        filename = f"{now.strftime('%Y%m%dT%H%M%S')}_{slug}.json"
        target = self.output_dir / filename
        with target.open("w", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False, indent=2)
        self._update_index(plan, target, record)
        return target

    def _update_index(
        self, plan: Dict[str, str], target: Path, record: Dict[str, Any]
    ) -> None:
        entry = {
            "query": plan["query"],
            "category": plan.get("category"),
            "template": plan.get("template"),
            "timestamp": record["timestamp"],
            "result_count": len(record["results"]),
            "file": str(target.name),
        }
        index = []
        if self.index_path.exists():
            with self.index_path.open("r", encoding="utf-8") as handle:
                try:
                    index = json.load(handle)
                except json.JSONDecodeError:
                    index = []
        index.append(entry)
        with self.index_path.open("w", encoding="utf-8") as handle:
            json.dump(index, handle, ensure_ascii=False, indent=2)


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return normalized.strip("-")[:64]


def load_config(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_plan(config: Dict[str, Any]) -> List[Dict[str, str]]:
    city = config.get("city", "")
    categories = config.get("categories", [])
    templates = config.get("query_templates", ["{category} {city}"])
    extra = config.get("extra_queries", [])

    plan: List[Dict[str, str]] = []
    for query_text in extra:
        if query_text:
            plan.append({"query": query_text, "category": None, "template": "extra"})
    for category in categories:
        for template in templates:
            query_text = template.format(category=category, city=city).strip()
            if not query_text:
                continue
            plan.append({
                "query": query_text,
                "category": category,
                "template": template,
            })

    deduped: List[Dict[str, str]] = []
    seen: Set[str] = set()
    for item in plan:
        query = item["query"]
        if query not in seen:
            deduped.append(item)
            seen.add(query)
    max_queries = config.get("max_queries", 0)
    if max_queries > 0:
        deduped = deduped[: max_queries]
    return deduped


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Brave Search queries to produce local-business lead data." 
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("config.json"),
        help="Path to the JSON config file",
    )
    parser.add_argument(
        "--token",
        help="Brave Search API token (falls back to BRAVE_API_KEY env or config)",
    )
    return parser.parse_args()


def resolve_token(args: argparse.Namespace, config: Dict[str, Any]) -> str:
    if args.token:
        return args.token
    env_token = os.environ.get("BRAVE_API_KEY")
    if env_token:
        return env_token
    file_token = config.get("api_key")
    if file_token:
        return file_token
    raise RuntimeError(
        "Brave Search API key is missing. Pass --token, set BRAVE_API_KEY, or store api_key in the config."
    )


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    token = resolve_token(args, config)
    finder = BraveLeadFinder(token, config)
    plan = build_plan(config)

    if not plan:
        print("No queries configured. Please edit the config first.")
        sys.exit(0)

    for index, entry in enumerate(plan, start=1):
        print(f"[{index}/{len(plan)}] Searching: {entry['query']}")
        try:
            record = finder.search(entry)
        except requests.HTTPError as exc:
            print(f"  → Failed ({exc}). Skipping.")
            continue
        except requests.RequestException as exc:
            print(f"  → Network error: {exc}. Retrying after delay.")
            time.sleep(2)
            continue
        output_path = finder.persist(entry, record)
        print(
            f"  → {len(record['results'])} hits saved to {output_path.relative_to(Path.cwd())}"
        )
        if finder.delay_seconds > 0:
            time.sleep(finder.delay_seconds)

    print(f"Run complete. Index file: {finder.index_path}")


if __name__ == "__main__":
    main()
