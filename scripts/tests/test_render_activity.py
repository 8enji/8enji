from scripts.render import render_activity_panel


ACTIVITY = list(range(1, 61))  # 60 increasing values


def test_activity_renders_correct_bar_count():
    svg = render_activity_panel(ACTIVITY, peak=60, streak_days=142, avg=14.3, x=14, y=500, w=680, h=354)
    # Each bar is a <rect>; count by counting class="bar-bar"
    assert svg.count('class="bar-bar"') == 60


def test_activity_renders_axis_labels():
    svg = render_activity_panel(ACTIVITY, peak=60, streak_days=142, avg=14.3, x=14, y=500, w=680, h=354)
    for label in ("60d", "45d", "30d", "15d", "today"):
        assert label in svg


def test_activity_renders_summary_strings():
    svg = render_activity_panel(ACTIVITY, peak=60, streak_days=142, avg=14.3, x=14, y=500, w=680, h=354)
    assert "60" in svg  # peak
    assert "142" in svg  # streak
    assert "14.3" in svg  # avg
