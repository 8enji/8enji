from scripts.render import render_languages_panel


LANGUAGES = [
    ("typescript", 42.0),
    ("python", 23.0),
    ("go", 14.0),
    ("rust", 11.0),
    ("lua", 6.0),
    ("other", 4.0),
]


def test_languages_renders_all_names():
    svg = render_languages_panel(LANGUAGES, x=708, y=60, w=778, h=426)
    for name, _ in LANGUAGES:
        assert name in svg


def test_languages_renders_percentages():
    svg = render_languages_panel(LANGUAGES, x=708, y=60, w=778, h=426)
    assert "42%" in svg
    assert "4%" in svg


def test_languages_header_says_last_12mo():
    svg = render_languages_panel(LANGUAGES, x=708, y=60, w=778, h=426)
    assert "12mo" in svg.lower() or "12MO" in svg
