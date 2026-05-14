from scripts.render import render_statusbar


CONFIG_STATUSBAR = {"cpu": "4%", "mem": "412mb", "net": "▲ 1.2mb/s", "version": "v2.6.0"}


def test_statusbar_shows_cpu_mem_net():
    svg = render_statusbar(CONFIG_STATUSBAR, clock="14:23:08", y=900)
    assert "cpu 4%" in svg.lower() or "CPU 4%" in svg
    assert "412mb" in svg
    assert "1.2mb/s" in svg


def test_statusbar_shows_version_and_clock():
    svg = render_statusbar(CONFIG_STATUSBAR, clock="14:23:08", y=900)
    assert "v2.6.0" in svg
    assert "14:23:08" in svg
