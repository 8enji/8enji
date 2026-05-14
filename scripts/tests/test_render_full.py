import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from scripts.render import render


FIXTURES = Path(__file__).parent / "fixtures"


def test_render_full_snapshot():
    config = yaml.safe_load((FIXTURES / "sample_config.yml").read_text())
    data = json.loads((FIXTURES / "sample_data.json").read_text())
    ts = datetime(2026, 5, 14, 14, 23, 8, tzinfo=timezone.utc)

    actual = render(config, data, ts)
    expected_path = FIXTURES / "expected.svg"
    expected = expected_path.read_text() if expected_path.exists() else ""

    if actual != expected:
        # Convenient debug: write actual.svg next to expected.svg
        (FIXTURES / "actual.svg").write_text(actual)
        assert actual == expected, "SVG differs from expected.svg (see actual.svg)"


def test_render_returns_full_svg_document():
    config = yaml.safe_load((FIXTURES / "sample_config.yml").read_text())
    data = json.loads((FIXTURES / "sample_data.json").read_text())
    ts = datetime(2026, 5, 14, 14, 23, 8, tzinfo=timezone.utc)

    svg = render(config, data, ts)
    assert svg.startswith("<?xml") or svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert 'viewBox="0 0 1500 1024"' in svg
