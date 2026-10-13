"""Precompute the analysis of each demo CSV and write it as a JSON fixture for the web /demo page.

Runs the same services as the worker (profile_csv, generate_insights_checked, _run_predictions)
and calls Anthropic for the insights. The API key is read from ANTHROPIC_API_KEY (environment or
apps/api/.env, through app.config.settings); it is only checked for presence and is never
printed or written.

Usage, from apps/api:
    python -m demo.generate_demo_fixture                 writes both fixtures
    python -m demo.generate_demo_fixture --dry-run       prints the insights and the check
                                                         report, writes nothing
    --model claude-opus-5-5                              uses another model (default: the app's)
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from app.config import settings
from app.services.insights_check import Dropped
from app.services.insights_llm import MODEL, generate_insights_checked
from app.services.profiling import profile_csv
from app.workers.tasks import _run_predictions

DEMO_DIR = Path(__file__).resolve().parent
FIXTURE_DIR = DEMO_DIR.parent.parent / "web" / "src" / "data" / "demo"
DATASETS = {
    "ventas.json": "demo_ventas_diarias.csv",
    "viviendas.json": "demo_viviendas.csv",
}


def _report(csv_name: str, model: str, insights: dict[str, Any], dropped: list[Dropped]) -> None:
    kept = [(category, item) for category, items in insights.items() for item in items]
    print(f"== {csv_name} ({model}): {len(kept)} kept, {len(dropped)} dropped ==")
    for category, item in kept:
        print(f"[{category}] {item['title']}: {item['description']}")
    for d in dropped:
        print(f"DROPPED [{d.category}] {d.title}: figures not in the data: {', '.join(d.missing)}")


def build_fixture(csv_name: str, model: str, dry_run: bool = False) -> dict[str, Any] | None:
    """Only what the analysis view renders: no ids, paths, timestamps or Supabase data."""
    content = (DEMO_DIR / csv_name).read_bytes()
    profile = profile_csv(content)
    insights, dropped = generate_insights_checked(profile, content, model=model)
    if dry_run:
        _report(csv_name, model, insights, dropped)
        return None
    if not any(insights.get(category) for category in insights):
        raise RuntimeError(f"{csv_name}: Anthropic returned no insights")
    return {
        "filename": csv_name,
        "size_bytes": len(content),
        "row_count": profile["row_count"],
        "column_count": profile["column_count"],
        "analysis": {
            "profile": profile,
            "insights": insights,
            "predictions": _run_predictions(content, profile),
        },
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m demo.generate_demo_fixture")
    parser.add_argument("--dry-run", action="store_true",
                        help="print the insights and the check report; write nothing")
    parser.add_argument("--model", default=MODEL, help=f"Claude model (default: {MODEL})")
    args = parser.parse_args(argv)

    # generate_insights_checked silently returns empty insights without a key: fail instead.
    if not settings.anthropic_api_key:
        sys.exit("ANTHROPIC_API_KEY is not set")
    if not args.dry_run:
        FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    for fixture_name, csv_name in DATASETS.items():
        fixture = build_fixture(csv_name, args.model, args.dry_run)
        if fixture is None:
            continue
        path = FIXTURE_DIR / fixture_name
        path.write_text(json.dumps(fixture, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{path.name}: {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
