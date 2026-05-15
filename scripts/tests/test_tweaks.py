from scripts.render import Tweaks


def test_tweaks_defaults_match_design():
    t = Tweaks()
    assert t.ascii_variant == "small"
    assert t.ascii_size_small == 12
    assert t.ascii_size_large == 7
    assert t.ascii_color == "#8b95a3"
    assert t.accent == "#b6e04f"
    assert t.font_size == 19
    assert t.pad_x == 88
    assert t.pad_y == 44
    assert t.gap == 44
    assert t.show_stats is True
    assert t.show_languages is True
    assert t.show_now is True
    assert t.show_palette is False
    assert t.show_statusbar is False
    assert t.show_rule is False


def test_ascii_size_follows_variant():
    assert Tweaks(ascii_variant="small", ascii_size_small=14).ascii_size == 14
    assert Tweaks(ascii_variant="large", ascii_size_large=8).ascii_size == 8


def test_from_config_reads_known_keys():
    cfg = {
        "tweaks": {
            "accent": "#ff00ff",
            "ascii_variant": "large",
            "ascii_size_large": 8,
            "show_palette": True,
        }
    }
    t = Tweaks.from_config(cfg)
    assert t.accent == "#ff00ff"
    assert t.ascii_variant == "large"
    assert t.ascii_size == 8
    assert t.show_palette is True
    # Unspecified keys keep defaults
    assert t.font_size == 19


def test_from_config_ignores_unknown_keys():
    cfg = {"tweaks": {"accent": "#ff00ff", "bogus_field": "ignored"}}
    t = Tweaks.from_config(cfg)
    assert t.accent == "#ff00ff"


def test_from_config_handles_missing_tweaks():
    assert Tweaks.from_config({}) == Tweaks()
    assert Tweaks.from_config({"tweaks": None}) == Tweaks()
