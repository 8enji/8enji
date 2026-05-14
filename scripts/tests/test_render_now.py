from scripts.render import render_now_panel


CFG = {
    "now": {
        "building": "a tiny static-site engine in rust",
        "listening": "tycho — awake (vinyl rip)",
        "learning": "zig · webgpu · papermaking",
        "reach": "@8enji · ben@bencharest.com",
    }
}


def test_now_renders_all_four_keys():
    svg = render_now_panel(CFG, x=14, y=870, w=1472, h=120)
    for k in ("building", "listening", "learning", "reach"):
        assert k in svg


def test_now_renders_all_values():
    svg = render_now_panel(CFG, x=14, y=870, w=1472, h=120)
    assert "static-site engine in rust" in svg
    assert "tycho" in svg
    assert "zig" in svg
    assert "@8enji" in svg


def test_now_panel_header():
    svg = render_now_panel(CFG, x=14, y=870, w=1472, h=120)
    assert "/etc/8enji.conf" in svg
