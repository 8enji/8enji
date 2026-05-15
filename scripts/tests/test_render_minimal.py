"""Tests for the minimal (neofetch-style) renderer."""

import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from scripts.render import Tweaks, _top_three_plus_other, render


FIXTURES = Path(__file__).parent / "fixtures"


def _load():
    config = yaml.safe_load((FIXTURES / "sample_config.yml").read_text())
    data = json.loads((FIXTURES / "sample_data.json").read_text())
    ts = datetime(2026, 5, 14, 14, 23, 8, tzinfo=timezone.utc)
    return config, data, ts


def test_renders_prompt_with_handle_and_machine():
    config, data, ts = _load()
    svg = render(config, data, ts)
    assert config["handle"] in svg
    assert config["machine"] in svg


def test_renders_kv_block_with_all_sysinfo_rows():
    config, data, ts = _load()
    svg = render(config, data, ts)
    for key in ("os", "host", "shell", "editor", "wm", "theme", "uptime"):
        assert f">{key}</text>" in svg
    assert config["website"] in svg
    assert config["me"]["theme"] in svg


def test_renders_all_six_stats():
    config, data, ts = _load()
    svg = render(config, data, ts)
    for key in ("repos", "stars", "followers", "commits", "streak", "loc"):
        assert f">{key}</text>" in svg
    assert str(data["public_repos"]) in svg
    assert str(data["activity_streak"]) + "d" in svg


def test_renders_top_three_languages_plus_other():
    config, data, ts = _load()
    svg = render(config, data, ts)
    # Top 3 from fixture: typescript, python, go. The language label renders
    # as `>{name} <tspan ...>{pct}%</tspan>` so we check for that prefix.
    assert ">typescript " in svg
    assert ">python " in svg
    assert ">go " in svg
    # rust/lua/other roll into a single 'other' bucket
    assert ">other " in svg
    # rust shouldn't appear as its own dot
    assert ">rust " not in svg


def test_top_three_plus_other_helper():
    langs = [
        ("typescript", 42.0),
        ("python", 23.0),
        ("go", 14.0),
        ("rust", 11.0),
        ("lua", 6.0),
        ("other", 4.0),
    ]
    result = _top_three_plus_other(langs)
    assert result == [
        ("typescript", 42.0),
        ("python", 23.0),
        ("go", 14.0),
        ("other", 21.0),
    ]


def test_top_three_plus_other_when_three_or_fewer():
    langs = [("a", 60.0), ("b", 40.0)]
    assert _top_three_plus_other(langs) == [("a", 60.0), ("b", 40.0)]


def test_renders_now_section_four_keys():
    config, data, ts = _load()
    svg = render(config, data, ts)
    for key in ("building", "learning", "listening", "reach"):
        assert f">{key}</text>" in svg


def test_statusbar_hidden_by_default():
    config, data, ts = _load()
    svg = render(config, data, ts)
    assert "ONLINE" not in svg
    assert "github.com" not in svg


def test_statusbar_visible_when_enabled():
    config, data, ts = _load()
    svg = render(config, data, ts, tweaks=Tweaks(show_statusbar=True))
    assert "ONLINE" in svg
    assert f'github.com/{config["handle"]}' in svg


def test_palette_hidden_by_default():
    config, data, ts = _load()
    svg = render(config, data, ts)
    # 1a1f29 is the palette's first swatch — should be absent
    assert "#1a1f29" not in svg


def test_palette_visible_when_enabled():
    config, data, ts = _load()
    svg = render(config, data, ts, tweaks=Tweaks(show_palette=True))
    assert "#1a1f29" in svg


def test_rule_hidden_by_default():
    config, data, ts = _load()
    svg = render(config, data, ts)
    # The rule is a long horizontal-bar run of unicode em dashes
    assert "─────" not in svg


def test_rule_visible_when_enabled():
    config, data, ts = _load()
    svg = render(config, data, ts, tweaks=Tweaks(show_rule=True))
    assert "─────" in svg


def test_hide_stats_section():
    config, data, ts = _load()
    on = render(config, data, ts, tweaks=Tweaks(show_stats=True))
    off = render(config, data, ts, tweaks=Tweaks(show_stats=False))
    assert ">repos</text>" in on
    assert ">repos</text>" not in off


def test_hide_languages_section():
    config, data, ts = _load()
    on = render(config, data, ts, tweaks=Tweaks(show_languages=True))
    off = render(config, data, ts, tweaks=Tweaks(show_languages=False))
    assert "typescript" in on
    assert "typescript" not in off


def test_hide_now_section():
    config, data, ts = _load()
    on = render(config, data, ts, tweaks=Tweaks(show_now=True))
    off = render(config, data, ts, tweaks=Tweaks(show_now=False))
    assert ">building</text>" in on
    assert ">building</text>" not in off


def test_canvas_width_is_1500():
    config, data, ts = _load()
    svg = render(config, data, ts)
    assert 'width="1500"' in svg
    assert 'viewBox="0 0 1500' in svg


def test_titlebar_text_matches_design():
    config, data, ts = _load()
    svg = render(config, data, ts)
    assert "-zsh" in svg
    assert "96×32" in svg


def test_ascii_size_changes_font_size_attribute():
    config, data, ts = _load()
    small = render(config, data, ts, tweaks=Tweaks(ascii_size=5))
    big = render(config, data, ts, tweaks=Tweaks(ascii_size=11))
    assert 'font-size="5"' in small
    assert 'font-size="11"' in big


def test_ascii_color_changes_fill_attribute():
    config, data, ts = _load()
    svg = render(config, data, ts, tweaks=Tweaks(ascii_color="#ff00ff"))
    assert 'fill="#ff00ff"' in svg


def test_accent_overrides_green():
    config, data, ts = _load()
    svg = render(config, data, ts, tweaks=Tweaks(accent="#ff00ff"))
    # The prompt @ and the 'go' lang dot use the green/accent slot
    assert "#ff00ff" in svg
