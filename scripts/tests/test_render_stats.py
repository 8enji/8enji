from scripts.render import render_stats_panel, format_compact, format_loc


STATS = {
    "repos": 42,
    "stars": 214,
    "followers": 89,
    "commits": 3128,
    "loc_bytes": 12_050_000,  # ~241k lines at 50 bytes/line
    "top_repos": [
        {"name": "static-rs", "language": "rust", "stars": 84},
        {"name": "tinybuf", "language": "go", "stars": 51},
        {"name": "dotfiles", "language": "lua", "stars": 37},
    ],
}


def test_format_compact():
    assert format_compact(3128) == "3,128"
    assert format_compact(214) == "214"


def test_format_loc():
    assert format_loc(12_050_000) == "241k"
    assert format_loc(500_000) == "10k"


def test_stats_renders_all_stat_labels():
    svg = render_stats_panel(STATS, x=708, y=500, w=778, h=354)
    for k in ("repos", "stars", "followers", "commits", "loc"):
        assert k in svg


def test_stats_renders_stat_values():
    svg = render_stats_panel(STATS, x=708, y=500, w=778, h=354)
    assert "42" in svg
    assert "214" in svg
    assert "89" in svg
    assert "3,128" in svg
    assert "241k" in svg


def test_stats_renders_top_repos():
    svg = render_stats_panel(STATS, x=708, y=500, w=778, h=354)
    for r in STATS["top_repos"]:
        assert r["name"] in svg
        assert r["language"] in svg
        assert str(r["stars"]) in svg


def test_stats_renders_live_indicator():
    svg = render_stats_panel(STATS, x=708, y=500, w=778, h=354)
    assert "live" in svg.lower() or "LIVE" in svg
