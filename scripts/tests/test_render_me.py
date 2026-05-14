from datetime import date
from scripts.render import render_me_panel


CONFIG = {
    "handle": "8enji",
    "machine": "dashboard",
    "website": "bencharest.com",
    "me": {
        "os": "macOS 15.4 · arm64",
        "shell": "zsh 5.9",
        "editor": "nvim · 0.10.2",
        "wm": "aerospace",
        "theme": "tokyonight-storm",
        "uptime_from": "2016-09-22",
    },
    "ascii_art": "AAAA\nBBBB\nCCCC\n",
}


def test_me_panel_renders_handle_and_machine():
    svg = render_me_panel(CONFIG, x=14, y=60, w=680, h=426, today=date(2026, 5, 14))
    assert "8enji" in svg
    assert "dashboard" in svg


def test_me_panel_renders_all_sysinfo_keys():
    svg = render_me_panel(CONFIG, x=14, y=60, w=680, h=426, today=date(2026, 5, 14))
    for key in ("host", "os", "shell", "editor", "wm", "theme", "uptime"):
        assert key in svg


def test_me_panel_renders_sysinfo_values():
    svg = render_me_panel(CONFIG, x=14, y=60, w=680, h=426, today=date(2026, 5, 14))
    assert "macOS 15.4" in svg
    assert "zsh 5.9" in svg
    assert "tokyonight-storm" in svg


def test_me_panel_renders_uptime():
    svg = render_me_panel(CONFIG, x=14, y=60, w=680, h=426, today=date(2026, 5, 14))
    # 2016-09-22 to 2026-05-14 = 3521 total days = 9 years, 236 days
    assert "9y" in svg
    assert "236d" in svg


def test_me_panel_renders_footer_status():
    svg = render_me_panel(CONFIG, x=14, y=60, w=680, h=426, today=date(2026, 5, 14))
    assert "online" in svg.lower()
    assert "bencharest.com" in svg


def test_me_panel_renders_ascii_lines():
    svg = render_me_panel(CONFIG, x=14, y=60, w=680, h=426, today=date(2026, 5, 14))
    assert "AAAA" in svg
    assert "BBBB" in svg
    assert "CCCC" in svg
