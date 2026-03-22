#!/usr/bin/env python3
"""Find email addresses for scraped leads by checking metadata and landing pages."""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Set

import requests

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
MAILTO_RE = re.compile(r"mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})", re.IGNORECASE)


class EmailHarvester:
    def __init__(
        self,
        timeout: float = 12.0,
        user_agent: str = "Clawdy/1.0 (lead-harvester)",
        dry_run: bool = False,
    ) -> None:
        self.timeout = timeout
        self.dry_run = dry_run
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})

    def run(
        self,
        data_files: Iterable[Path],
        *,
        max_results_per_file: int | None = None,
        output_path: Path,
    ) -> Path:
        files_summary: List[dict] = []
        for source in data_files:
            if not source.exists():
                continue
            with source.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)

            results = payload.get("results", [])
            limited = results[:max_results_per_file] if max_results_per_file else results
            entries = []
            for result in limited:
                entry = self._process_result(result)
                entries.append(entry)

            files_summary.append(
                {
                    "file": str(source.name),
                    "query": payload.get("query"),
                    "template": payload.get("template"),
                    "category": payload.get("category"),
                    "entries": entries,
                }
            )
        output_payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "files": files_summary,
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as handle:
            json.dump(output_payload, handle, ensure_ascii=False, indent=2)
        return output_path

    def _process_result(self, result: dict) -> dict:
        extracted: Set[str] = set()
        notes: List[str] = []
        for field in ("title", "description", "snippet"):
            text = result.get(field)
            if text:
                extracted.update(self._extract_from_text(text))
        url = result.get("url")
        status = "skipped"
        if url:
            if self.dry_run:
                notes.append("fetch skipped (dry run)")
                status = "dry-run"
            else:
                page_body, error = self._fetch(url)
                if error:
                    notes.append(f"fetch failed: {error}")
                    status = "error"
                else:
                    extracted.update(self._extract_from_text(page_body))
                    status = "fetched"
        return {
            "title": result.get("title"),
            "url": url,
            "emails": sorted(extracted),
            "status": status,
            "notes": notes,
        }

    def _fetch(self, url: str) -> tuple[Optional[str], Optional[str]]:
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text, None
        except requests.RequestException as exc:
            return None, str(exc)

    @staticmethod
    def _extract_from_text(text: str) -> Set[str]:
        emails = set(EMAIL_RE.findall(text))
        emails.update(MAILTO_RE.findall(text))
        return emails


def list_files(data_dir: Path) -> List[Path]:
    index_path = data_dir / "index.json"
    if index_path.exists():
        with index_path.open("r", encoding="utf-8") as handle:
            index = json.load(handle)
        candidates: List[Path] = []
        for entry in index:
            filename = entry.get("file")
            if filename:
                candidates.append(data_dir / filename)
        return [path for path in candidates if path.exists()]
    return sorted(data_dir.glob("*.json"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan lead URLs to discover email addresses."
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("leads/data"),
        help="Directory where lead JSON files live.",
    )
    parser.add_argument(
        "--files",
        nargs="+",
        help="Specific data files to scan (relative to --data-dir).",
    )
    parser.add_argument(
        "--max-results-per-file",
        type=int,
        help="Limit how many results to scan per lead file (default: all).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("leads/data/emails.json"),
        help="Where to write the harvested addresses.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=12.0,
        help="Timeout in seconds for fetching each lead URL.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip HTTP requests and only inspect existing metadata.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data_dir = args.data_dir
    if args.files:
        files = [data_dir / name for name in args.files]
    else:
        files = list_files(data_dir)
    harvester = EmailHarvester(timeout=args.timeout, dry_run=args.dry_run)
    output_path = harvester.run(
        files,
        max_results_per_file=args.max_results_per_file,
        output_path=args.output,
    )
    print(f"Emails written to {output_path}")


if __name__ == "__main__":
    main()
