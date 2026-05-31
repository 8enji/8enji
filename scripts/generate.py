"""Entry point: load config, fetch GitHub data, render SVG, write to disk."""

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

import yaml

from scripts.github_data import GitHubClient
from scripts.render import render


REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config.yml"
OUTPUT_PATH = REPO_ROOT / "dashboard.svg"


def _format_uptime(uptime_from: str, today: date) -> str:
    start = date.fromisoformat(uptime_from)
    delta_days = (today - start).days
    return f"{delta_days // 365}y {delta_days % 365}d"


def _adapt_github_data(gd: dict, uptime: str) -> dict:
    """Translate github_data.fetch_all() output to the renderer's data shape."""
    languages = {name: pct for name, pct in gd.get("languages", [])}
    return {
        "repos":     gd.get("public_repos", 0),
        "stars":     gd.get("total_stars", 0),
        "followers": gd.get("followers", 0),
        "commits":   gd.get("total_commits", 0),
        "streak":    gd.get("activity_streak", 0),
        # Bytes → approximate LOC at ~50 bytes/line, then _humanize_loc handles the suffix.
        "loc":       gd.get("total_loc_bytes", 0) // 50,
        "languages": languages,
        "uptime":    uptime,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Print SVG to stdout instead of writing to disk")
    parser.add_argument("--from-fixture", action="store_true",
                        help="Use sample fixture data instead of hitting the GitHub API")
    args = parser.parse_args()

    config = yaml.safe_load(CONFIG_PATH.read_text())
    today = date.today()

    if args.from_fixture:
        fixtures = Path(__file__).parent / "tests" / "fixtures"
        data = json.loads((fixtures / "sample_data.json").read_text())
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            print("error: GITHUB_TOKEN env var required", file=sys.stderr)
            return 2
        client = GitHubClient(
            token=token,
            user=config["me"]["handle"],
            include_orgs=config["me"].get("include_orgs", []),
        )
        gd = client.fetch_all(today=today)
        uptime = _format_uptime(config["me"]["uptime_from"], today)
        data = _adapt_github_data(gd, uptime)

    svg = render(config, data)

    if args.dry_run:
        sys.stdout.write(svg)
    else:
        OUTPUT_PATH.write_text(svg)
        print(f"wrote {OUTPUT_PATH} ({len(svg)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
