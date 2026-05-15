"""Local preview server for tweaking dashboard parameters interactively.

Usage:
    python -m scripts.preview_server [--port 8000]

Open http://localhost:8000 to adjust accent color, font sizes, density,
visibility toggles. The preview re-renders as you drag sliders. Copy the
YAML block from the side panel into config.yml when you're happy.
"""

import argparse
import json
from dataclasses import fields
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yaml

from scripts.render import Tweaks, render

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config.yml"
FIXTURE_PATH = REPO_ROOT / "scripts" / "tests" / "fixtures" / "sample_data.json"
TEMPLATE_PATH = Path(__file__).parent / "preview.html"


def _load_config() -> dict:
    return yaml.safe_load(CONFIG_PATH.read_text())


def _load_data() -> dict:
    return json.loads(FIXTURE_PATH.read_text())


def _tweaks_to_dict(t: Tweaks) -> dict:
    return {f.name: getattr(t, f.name) for f in fields(t)}


def _override_from_qs(tweaks: Tweaks, qs: dict[str, list[str]]) -> Tweaks:
    for f in fields(tweaks):
        if f.name not in qs:
            continue
        raw = qs[f.name][0]
        current = getattr(tweaks, f.name)
        if isinstance(current, bool):
            setattr(tweaks, f.name, raw.lower() in ("true", "1", "on", "yes"))
        elif isinstance(current, int):
            setattr(tweaks, f.name, int(float(raw)))
        elif isinstance(current, float):
            setattr(tweaks, f.name, float(raw))
        else:
            setattr(tweaks, f.name, raw)
    return tweaks


class PreviewHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send(self, status: int, body: str, content_type: str):
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self):
        url = urlparse(self.path)
        try:
            if url.path == "/":
                self._send(200, TEMPLATE_PATH.read_text(), "text/html")
                return
            if url.path == "/api/tweaks":
                t = Tweaks.from_config(_load_config())
                self._send(200, json.dumps(_tweaks_to_dict(t)), "application/json")
                return
            if url.path == "/render.svg":
                config = _load_config()
                data = _load_data()
                tweaks = Tweaks.from_config(config)
                tweaks = _override_from_qs(tweaks, parse_qs(url.query))
                svg = render(config, data, datetime.now(timezone.utc), tweaks=tweaks)
                self._send(200, svg, "image/svg+xml")
                return
            self._send(404, "not found", "text/plain")
        except Exception as e:
            self._send(500, f"error: {e}", "text/plain")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), PreviewHandler)
    url = f"http://{args.host}:{args.port}"
    print(f"Preview server running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
