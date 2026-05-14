from scripts.render import render_panel_frame


def test_panel_frame_has_border_and_header():
    svg = render_panel_frame(x=14, y=60, w=680, h=400, label="me", right="/etc/8enji.png")
    assert "me" in svg.lower()
    assert "/etc/8enji.png" in svg
    assert 'rx="9"' in svg  # rounded border
