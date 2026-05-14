"""Entry point: load config, fetch GitHub data, render SVG, write to disk."""

import argparse
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

from scripts.github_data import GitHubClient
from scripts.render import render


REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config.yml"
OUTPUT_PATH = REPO_ROOT / "dashboard.svg"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Print SVG to stdout instead of writing to disk")
    parser.add_argument("--from-fixture", action="store_true",
                        help="Use sample fixture data instead of hitting the GitHub API")
    args = parser.parse_args()

    config = yaml.safe_load(CONFIG_PATH.read_text())

    if args.from_fixture:
        fixtures = Path(__file__).parent / "tests" / "fixtures"
        data = json.loads((fixtures / "sample_data.json").read_text())
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            print("error: GITHUB_TOKEN env var required", file=sys.stderr)
            return 2
        client = GitHubClient(token=token, user=config["handle"])
        data = client.fetch_all(today=date.today())

    timestamp = datetime.now(timezone.utc)
    svg = render(config, data, timestamp)

    if args.dry_run:
        sys.stdout.write(svg)
    else:
        OUTPUT_PATH.write_text(svg)
        print(f"wrote {OUTPUT_PATH} ({len(svg)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
