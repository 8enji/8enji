"""Tests for the minimal (neofetch-style) renderer."""

import json
from copy import deepcopy
from pathlib import Path

import yaml

from scripts.render import render


FIXTURES = Path(__file__).parent / "fixtures"


def _load():
    config = yaml.safe_load((FIXTURES / "sample_config.yml").read_text())
    data = json.loads((FIXTURES / "sample_data.json").read_text())
    return config, data


def _with_tweaks(config: dict, **overrides) -> dict:
    out = deepcopy(config)
    out.setdefault("tweaks", {}).update(overrides)
    return out


def test_renders_prompt_with_handle_and_host_short():
    config, data = _load()
    svg = render(config, data)
    assert config["me"]["handle"] in svg
    assert config["me"]["host_short"] in svg


def test_renders_kv_block_with_all_sysinfo_rows():
    config, data = _load()
    svg = render(config, data)
    for key in ("os", "host", "shell", "editor", "theme", "uptime"):
        assert f">{key}</text>" in svg
    # 'wm' is dropped in the minimal redesign
    assert ">wm</text>" not in svg
    assert config["me"]["host"] in svg
    assert config["me"]["theme"] in svg
    assert data["uptime"] in svg


def test_renders_all_six_stats():
    config, data = _load()
    svg = render(config, data)
    for key in ("repos", "stars", "followers", "commits", "streak", "loc"):
        assert f">{key}</text>" in svg
    assert f'>{data["repos"]}</text>' in svg
    assert f'{data["streak"]}d' in svg
    # stars are formatted with an orange ★ glyph
    assert "★" in svg


def test_renders_top_three_languages_plus_other():
    config, data = _load()
    svg = render(config, data)
    # Top 3 from fixture: typescript, python, go. Each lang renders as
    # `>{name} <tspan ...>{pct}%</tspan>`.
    assert ">typescript " in svg
    assert ">python " in svg
    assert ">go " in svg
    # rust/lua/other roll into a single 'other' bucket
    assert ">other " in svg
    # rust shouldn't appear as its own dot
    assert ">rust " not in svg


def test_renders_now_section_four_keys():
    config, data = _load()
    svg = render(config, data)
    for key in ("building", "learning", "listening", "reach"):
        assert f">{key}</text>" in svg


def test_statusbar_hidden_by_default():
    config, data = _load()
    svg = render(config, data)
    assert "ONLINE" not in svg
    assert config["me"]["github_url"] not in svg


def test_statusbar_visible_when_enabled():
    config, data = _load()
    svg = render(_with_tweaks(config, show_statusbar=True), data)
    assert "ONLINE" in svg
    assert config["me"]["github_url"] in svg


def test_palette_hidden_by_default():
    config, data = _load()
    svg = render(config, data)
    # 1a1f29 is the palette's first swatch — should be absent
    assert "#1a1f29" not in svg


def test_palette_visible_when_enabled():
    config, data = _load()
    svg = render(_with_tweaks(config, show_palette=True), data)
    assert "#1a1f29" in svg


RULE_SIGNATURE = 'stroke="#3f4753" stroke-width="1"/>'  # solid rule, distinct from stats dotted lines


def test_rule_hidden_by_default():
    config, data = _load()
    svg = render(config, data)
    assert RULE_SIGNATURE not in svg


def test_rule_visible_when_enabled():
    config, data = _load()
    svg = render(_with_tweaks(config, show_rule=True), data)
    assert RULE_SIGNATURE in svg


def test_hide_stats_section():
    config, data = _load()
    on = render(_with_tweaks(config, show_stats=True), data)
    off = render(_with_tweaks(config, show_stats=False), data)
    assert ">repos</text>" in on
    assert ">repos</text>" not in off


def test_hide_languages_section():
    config, data = _load()
    on = render(_with_tweaks(config, show_languages=True), data)
    off = render(_with_tweaks(config, show_languages=False), data)
    assert "typescript" in on
    assert "typescript" not in off


def test_hide_now_section():
    config, data = _load()
    on = render(_with_tweaks(config, show_now=True), data)
    off = render(_with_tweaks(config, show_now=False), data)
    assert ">building</text>" in on
    assert ">building</text>" not in off


def test_canvas_width_is_1280():
    config, data = _load()
    svg = render(config, data)
    assert 'width="1280"' in svg
    assert 'viewBox="0 0 1280' in svg


def test_titlebar_text_matches_design():
    config, data = _load()
    svg = render(config, data)
    assert "-zsh" in svg
    assert "96×32" in svg


def test_ascii_size_changes_font_size_attribute():
    config, data = _load()
    small = render(_with_tweaks(config, ascii_size=5), data)
    big = render(_with_tweaks(config, ascii_size=11), data)
    assert 'font-size="5"' in small
    assert 'font-size="11"' in big


def test_ascii_color_changes_fill_attribute():
    config, data = _load()
    svg = render(_with_tweaks(config, ascii_color="#ff00ff"), data)
    assert 'fill="#ff00ff"' in svg


def test_accent_overrides_green():
    config, data = _load()
    # Status bar dot uses the accent — enable to surface it
    svg = render(
        _with_tweaks(config, accent="#ff00ff", show_statusbar=True),
        data,
    )
    assert "#ff00ff" in svg
