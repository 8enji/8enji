from scripts.render import render_chrome, CANVAS_W


def test_chrome_contains_traffic_lights():
    svg = render_chrome(title_left="8enji", title_right="dashboard")
    assert 'fill="#ff5f57"' in svg
    assert 'fill="#febc2e"' in svg
    assert 'fill="#28c840"' in svg


def test_chrome_contains_title_text():
    svg = render_chrome(title_left="8enji", title_right="dashboard")
    assert "8enji.dashboard" in svg or ("8enji" in svg and "dashboard" in svg)


def test_canvas_width_is_1500():
    assert CANVAS_W == 1500
