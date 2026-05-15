import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from scripts.render import Tweaks, render


FIXTURES = Path(__file__).parent / "fixtures"


def _load():
    config = yaml.safe_load((FIXTURES / "sample_config.yml").read_text())
    data = json.loads((FIXTURES / "sample_data.json").read_text())
    ts = datetime(2026, 5, 14, 14, 23, 8, tzinfo=timezone.utc)
    return config, data, ts


def test_tweaks_defaults():
    t = Tweaks()
    assert t.accent == "#b6e04f"
    assert t.show_statusbar is True
    assert t.font_scale == 1.0


def test_from_config_reads_tweaks_section():
    config = {"tweaks": {"accent": "#ff00ff", "ascii_size": 9}}
    t = Tweaks.from_config(config)
    assert t.accent == "#ff00ff"
    assert t.ascii_size == 9
    # Unspecified keys keep defaults
    assert t.show_statusbar is True


def test_from_config_ignores_unknown_keys():
    config = {"tweaks": {"accent": "#ff00ff", "bogus": 42}}
    t = Tweaks.from_config(config)
    assert t.accent == "#ff00ff"


def test_from_config_handles_missing_tweaks():
    t = Tweaks.from_config({})
    assert t == Tweaks()


def test_accent_replaces_default_green_throughout_svg():
    config, data, ts = _load()
    svg = render(config, data, ts, tweaks=Tweaks(accent="#ff00ff"))
    assert "#b6e04f" not in svg
    assert "#ff00ff" in svg


def test_show_statusbar_false_omits_statusbar():
    config, data, ts = _load()
    svg_with = render(config, data, ts, tweaks=Tweaks(show_statusbar=True))
    svg_without = render(config, data, ts, tweaks=Tweaks(show_statusbar=False))
    assert "CPU" in svg_with
    assert "CPU" not in svg_without


def test_show_sysinfo_false_omits_sysinfo_block():
    config, data, ts = _load()
    svg_with = render(config, data, ts, tweaks=Tweaks(show_sysinfo=True))
    svg_without = render(config, data, ts, tweaks=Tweaks(show_sysinfo=False))
    assert "macOS" in svg_with
    assert "macOS" not in svg_without


def test_show_second_now_col_false_omits_learning_and_reach():
    config, data, ts = _load()
    svg_with = render(config, data, ts, tweaks=Tweaks(show_second_now_col=True))
    svg_without = render(config, data, ts, tweaks=Tweaks(show_second_now_col=False))
    assert "learning" in svg_with
    assert "learning" not in svg_without
    assert "reach" in svg_with
    assert "reach" not in svg_without


def test_font_scale_multiplies_font_size_values():
    config, data, ts = _load()
    svg = render(config, data, ts, tweaks=Tweaks(font_scale=2.0))
    # Original "font-size=\"13\"" becomes "font-size=\"26\"" after 2x scale
    assert 'font-size="26"' in svg
    assert 'font-size="13"' not in svg


def test_ascii_size_changes_ascii_text_font_size():
    config, data, ts = _load()
    svg_small = render(config, data, ts, tweaks=Tweaks(ascii_size=3))
    svg_big = render(config, data, ts, tweaks=Tweaks(ascii_size=11))
    assert 'font-size="3"' in svg_small
    assert 'font-size="11"' in svg_big


def test_bar_height_changes_language_bar_height():
    config, data, ts = _load()
    svg_thin = render(config, data, ts, tweaks=Tweaks(bar_height=8))
    svg_thick = render(config, data, ts, tweaks=Tweaks(bar_height=22))
    assert 'height="8"' in svg_thin
    assert 'height="22"' in svg_thick
