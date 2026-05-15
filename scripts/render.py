"""SVG renderer for the 8enji minimal dashboard (neofetch-style).

Pure functions: no I/O, no global state. Mirrors the design at
readme/project/readme-minimal.html in the design handoff — ASCII
portrait on the left, structured info column on the right.
"""

import re
from dataclasses import dataclass, fields
from datetime import date


CANVAS_W = 1400
PADDING_X = 48
PADDING_TOP = 40
PADDING_BOTTOM = 44
TITLEBAR_H = 45
STATUSBAR_H = 36


COLORS = {
    "bg_outer": "#07090d",
    "bg": "#0e1218",
    "text": "#cdd6e1",
    "text_dim": "#8b95a3",
    "muted": "#5a6473",
    "muted_soft": "#3f4753",
    "green": "#b6e04f",
    "purple": "#c8a2ff",
    "orange": "#f1c47a",
    "pink": "#ee557d",
    "ts": "#5fb7ff",
    "rust": "#f1c47a",
    "lua": "#ee557d",
    "cyan": "#5fd9c8",
    "palette_bg": "#1a1f29",
}

FONT_STACK = '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'

# Approximate horizontal character width as a fraction of font-size for
# monospace. JetBrains Mono ~0.6; we use 0.55 to leave a little air.
MONO_CHAR_W = 0.55

LANG_DOT_COLORS = {
    "typescript":  COLORS["ts"],
    "javascript":  "#f1e05a",
    "python":      COLORS["purple"],
    "go":          COLORS["green"],
    "rust":        COLORS["rust"],
    "lua":         COLORS["lua"],
    "java":        "#f89820",
    "kotlin":      "#a97bff",
    "swift":       "#ff7e3b",
    "ruby":        "#cc342d",
    "php":         "#787cb5",
    "html":        "#e44d26",
    "css":         "#5fb7ff",
    "scss":        "#cc6699",
    "shell":       "#89e051",
    "bash":        "#89e051",
    "c":           "#a8b9cc",
    "c++":         "#f34b7d",
    "c#":          "#9b4dca",
    "vue":         "#41b883",
    "svelte":      "#ff3e00",
    "dart":        "#00b4ab",
    "r":           "#5fb7ff",
    "scala":       "#dc6868",
    "haskell":     "#a78bfa",
    "elixir":      "#a97bff",
    "perl":        "#0fc4dc",
    "matlab":      "#e16737",
    "objective-c": "#438eff",
    "sql":         "#e38c00",
    "markdown":    COLORS["text_dim"],
    "dockerfile":  "#0db7ed",
    "yaml":        "#e5c07b",
    "json":        "#cdd6e1",
    "tex":         "#82b541",
    "latex":       "#82b541",
}


@dataclass
class Tweaks:
    """Visual knobs for the minimal layout. Defaults match the design's
    saved tweaks block (asciiSize=9, fontSize=17, gap=60, showRule=false,
    showPalette=false, showStatusBar=false)."""

    ascii_size: int = 9
    ascii_color: str = "#8b95a3"
    accent: str = "#b6e04f"
    font_size: int = 17
    gap: int = 60
    show_stats: bool = True
    show_languages: bool = True
    show_now: bool = True
    show_palette: bool = False
    show_statusbar: bool = False
    show_rule: bool = False

    @classmethod
    def from_config(cls, config: dict) -> "Tweaks":
        raw = config.get("tweaks") or {}
        valid = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in raw.items() if k in valid})


def _escape_xml(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _format_uptime(uptime_from: str, today: date) -> str:
    start = date.fromisoformat(uptime_from)
    delta_days = (today - start).days
    return f"{delta_days // 365}y {delta_days % 365}d"


def format_compact(n: int) -> str:
    return f"{n:,}"


def format_loc(total_bytes: int) -> str:
    lines = total_bytes // 50
    return f"{lines // 1000}k"


def _lang_color(name: str, accent: str | None = None) -> str:
    """Look up a color for a language name (case-insensitive).
    `accent` overrides the 'go' default so swapping accent recolors
    the green dot consistently."""
    n = name.lower()
    if n == "go" and accent:
        return accent
    if n == "other":
        return COLORS["muted"]
    return LANG_DOT_COLORS.get(n, COLORS["muted"])


def _top_three_plus_other(
    languages: list[tuple[str, float]],
) -> list[tuple[str, float]]:
    """Roll everything past the top 3 into 'other'."""
    top = languages[:3]
    rest_pct = sum(p for _, p in languages[3:])
    if rest_pct > 0:
        top.append(("other", rest_pct))
    return top


def render(
    config: dict,
    data: dict,
    timestamp,
    tweaks: "Tweaks | None" = None,
) -> str:
    """Render the full minimal dashboard SVG."""
    if tweaks is None:
        tweaks = Tweaks.from_config(config)

    today = timestamp.date()

    colors = dict(COLORS)
    colors["green"] = tweaks.accent

    fs = tweaks.font_size

    # ASCII column dimensions
    ascii_lines = config["ascii_art"].rstrip("\n").split("\n")
    max_line_len = max((len(l) for l in ascii_lines), default=0)
    ascii_w = int(max_line_len * tweaks.ascii_size * MONO_CHAR_W)
    ascii_line_h = tweaks.ascii_size  # line-height: 1 per design
    ascii_h = len(ascii_lines) * ascii_line_h

    # Layout
    body_x = PADDING_X
    body_y = TITLEBAR_H + PADDING_TOP
    info_x = body_x + ascii_w + tweaks.gap

    parts: list[str] = []
    info_y = body_y  # tracks the top edge of the next section in the info column

    # ── prompt: "8enji@dashboard" ────────────────────────────────
    prompt_fs = fs * 1.14
    baseline = info_y + prompt_fs
    parts.append(
        f'<text x="{info_x}" y="{baseline:.1f}" font-family=\'{FONT_STACK}\' '
        f'font-size="{prompt_fs:.2f}" fill="{colors["green"]}">'
        f'<tspan font-weight="500" fill="{colors["text"]}">'
        f'{_escape_xml(config["handle"])}</tspan>'
        f'<tspan fill="{colors["text_dim"]}">@</tspan>'
        f'<tspan font-weight="500" fill="{colors["text"]}">'
        f'{_escape_xml(config["machine"])}</tspan>'
        f"</text>"
    )
    info_y = int(baseline + 4)  # margin-bottom

    # ── rule (toggleable) ────────────────────────────────────────
    if tweaks.show_rule:
        baseline = info_y + fs
        parts.append(
            f'<text x="{info_x}" y="{baseline}" font-family=\'{FONT_STACK}\' '
            f'font-size="{fs}" fill="{colors["muted_soft"]}">'
            f"─────────────────────────</text>"
        )
        info_y = int(baseline + 4)

    info_y += 10  # spacer after prompt block

    # ── kv block: os / host / shell / editor / wm / theme / uptime
    me = config["me"]
    kv_rows = [
        ("os", me["os"]),
        ("host", config["website"]),
        ("shell", me["shell"]),
        ("editor", me["editor"]),
        ("wm", me["wm"]),
        ("theme", me["theme"]),
        ("uptime", _format_uptime(me["uptime_from"], today)),
    ]
    kv_col_w = int(fs * 5.5)  # ~96px at font_size 17
    kv_key_x = info_x
    kv_val_x = info_x + kv_col_w + 18
    kv_line_h = fs + 4
    parts.append(
        _render_kv_block(kv_rows, kv_key_x, kv_val_x, info_y, fs, kv_line_h, colors)
    )
    info_y += len(kv_rows) * kv_line_h + 22

    # ── stats (toggleable) ──────────────────────────────────────
    if tweaks.show_stats:
        info_y = _render_section_title(parts, "stats", info_x, info_y, fs, colors)
        stat_pairs = [
            [("repos", str(data["public_repos"])),
             ("commits", format_compact(data["total_commits"]))],
            [("stars", _stars_with_glyph(data["total_stars"], colors)),
             ("streak", f'{data["activity_streak"]}d')],
            [("followers", str(data["followers"])),
             ("loc", format_loc(data["total_loc_bytes"]))],
        ]
        col_count = 2
        info_w = CANVAS_W - info_x - PADDING_X
        col_gap = 32
        col_w = (info_w - col_gap * (col_count - 1)) // col_count
        row_h = fs + 6
        for row_idx, pair in enumerate(stat_pairs):
            row_y = info_y + fs + row_idx * row_h
            for col_idx, (k, v_text) in enumerate(pair):
                x = info_x + col_idx * (col_w + col_gap)
                parts.append(
                    f'<text x="{x}" y="{row_y}" font-family=\'{FONT_STACK}\' '
                    f'font-size="{fs}" fill="{colors["text_dim"]}">{_escape_xml(k)}</text>'
                )
                parts.append(
                    f'<text x="{x + col_w}" y="{row_y}" font-family=\'{FONT_STACK}\' '
                    f'font-size="{fs}" fill="{colors["text"]}" text-anchor="end" '
                    f'font-variant-numeric="tabular-nums">{v_text}</text>'
                )
                parts.append(
                    f'<line x1="{x}" y1="{row_y + 4}" x2="{x + col_w}" y2="{row_y + 4}" '
                    f'stroke="rgba(148,163,184,0.07)" stroke-width="1" stroke-dasharray="1 3"/>'
                )
        info_y += len(stat_pairs) * row_h + 18

    # ── languages (toggleable, top 3 + other) ───────────────────
    if tweaks.show_languages:
        info_y = _render_section_title(
            parts, "languages · last 12mo", info_x, info_y, fs, colors
        )
        all_langs = [tuple(l) for l in data["languages"]]
        langs = _top_three_plus_other(all_langs)
        lang_fs = fs * 0.93
        baseline = info_y + lang_fs
        dot_size = 10
        gap_between = 22
        x = info_x
        for name, pct in langs:
            color = _lang_color(name, accent=tweaks.accent)
            parts.append(
                f'<rect x="{x:.1f}" y="{baseline - lang_fs * 0.85:.1f}" '
                f'width="{dot_size}" height="{dot_size}" rx="2" fill="{color}"/>'
            )
            label = f"{name} {int(round(pct))}%"
            label_x = x + dot_size + 8
            parts.append(
                f'<text x="{label_x:.1f}" y="{baseline:.1f}" font-family=\'{FONT_STACK}\' '
                f'font-size="{lang_fs:.2f}" fill="{colors["text"]}">'
                f'{_escape_xml(name)} '
                f'<tspan fill="{colors["text_dim"]}">{int(round(pct))}%</tspan></text>'
            )
            label_w = len(label) * lang_fs * MONO_CHAR_W + dot_size + 8
            x += label_w + gap_between
        info_y = int(baseline + 18)

    # ── now (toggleable) ────────────────────────────────────────
    if tweaks.show_now:
        info_y = _render_section_title(parts, "now", info_x, info_y, fs, colors)
        now = config["now"]
        now_rows = [
            ("building", now["building"]),
            ("learning", now["learning"]),
            ("listening", now["listening"]),
            ("reach", now["reach"]),
        ]
        parts.append(
            _render_kv_block(
                now_rows, kv_key_x, kv_val_x, info_y, fs, kv_line_h, colors
            )
        )
        info_y += len(now_rows) * kv_line_h + 18

    # ── palette (toggleable, off by default) ────────────────────
    if tweaks.show_palette:
        sw_w, sw_h = 28, 14
        palette_seq = [
            colors["palette_bg"],
            colors["pink"],
            colors["green"],
            colors["orange"],
            colors["ts"],
            colors["purple"],
            colors["cyan"],
            colors["text"],
        ]
        for i, c in enumerate(palette_seq):
            parts.append(
                f'<rect x="{info_x + i * sw_w}" y="{info_y}" '
                f'width="{sw_w}" height="{sw_h}" fill="{c}"/>'
            )
        info_y += sw_h + 12

    # ── ASCII portrait (left column) ────────────────────────────
    ascii_tspans = "".join(
        f'<tspan x="{body_x}" y="{body_y + (i + 1) * ascii_line_h}">'
        f"{_escape_xml(line)}</tspan>"
        for i, line in enumerate(ascii_lines)
    )
    ascii_block = (
        f"<text font-family='{FONT_STACK}' "
        f'font-size="{tweaks.ascii_size}" fill="{tweaks.ascii_color}" '
        f'xml:space="preserve" font-weight="500">{ascii_tspans}</text>'
    )

    # ── canvas height ───────────────────────────────────────────
    content_bottom = max(info_y, body_y + ascii_h)
    canvas_h = content_bottom + PADDING_BOTTOM
    if tweaks.show_statusbar:
        canvas_h += STATUSBAR_H

    chrome = _render_chrome(
        title=f'{_escape_xml(config["handle"])} — -zsh — 96×32',
        canvas_h=canvas_h,
    )
    statusbar = ""
    if tweaks.show_statusbar:
        statusbar = _render_statusbar(
            y=canvas_h - STATUSBAR_H,
            version=config.get("statusbar", {}).get("version", "v2.6.0"),
            handle=config["handle"],
            colors=colors,
        )

    svg = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {CANVAS_W} {canvas_h}" '
        f'width="{CANVAS_W}" height="{canvas_h}" '
        f"font-family='{FONT_STACK}'>"
        f'<rect width="100%" height="100%" fill="{colors["bg_outer"]}"/>'
        f"{chrome}"
        f"{ascii_block}"
        f"{''.join(parts)}"
        f"{statusbar}"
        f"</svg>"
    )
    return svg


def _stars_with_glyph(n: int, colors: dict) -> str:
    """Render a star count with the orange '★' tspan appended."""
    return f'{n} <tspan fill="{colors["orange"]}">★</tspan>'


def _render_section_title(
    parts: list[str], label: str, x: int, y: int, fs: int, colors: dict
) -> int:
    """Emit a small uppercase section title and return the next y."""
    title_fs = fs * 0.82
    baseline = y + title_fs
    parts.append(
        f'<text x="{x}" y="{baseline:.1f}" font-family=\'{FONT_STACK}\' '
        f'font-size="{title_fs:.2f}" fill="{colors["muted"]}" font-weight="600" '
        f'letter-spacing="{title_fs * 0.16:.2f}" '
        f'text-transform="uppercase">{_escape_xml(label)}</text>'
    )
    return int(baseline + 10)


def _render_kv_block(
    rows: list[tuple[str, str]],
    key_x: int,
    val_x: int,
    start_y: int,
    fs: int,
    line_h: int,
    colors: dict,
) -> str:
    """Render a key/value grid with purple keys and light values."""
    out = []
    for i, (k, v) in enumerate(rows):
        row_y = start_y + fs + i * line_h
        out.append(
            f'<text x="{key_x}" y="{row_y}" font-family=\'{FONT_STACK}\' '
            f'font-size="{fs}" fill="{colors["purple"]}">{_escape_xml(k)}</text>'
        )
        out.append(
            f'<text x="{val_x}" y="{row_y}" font-family=\'{FONT_STACK}\' '
            f'font-size="{fs}" fill="{colors["text"]}">{_escape_xml(v)}</text>'
        )
    return "".join(out)


def _render_chrome(title: str, canvas_h: int) -> str:
    """Window border + titlebar (traffic lights + centered title)."""
    return (
        f'<g class="chrome">'
        f'<rect x="0" y="0" width="{CANVAS_W}" height="{canvas_h}" '
        f'rx="14" ry="14" fill="{COLORS["bg"]}" '
        f'stroke="rgba(255,255,255,0.06)" stroke-width="1"/>'
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" '
        f'stroke="rgba(255,255,255,0.05)" stroke-width="1"/>'
        f'<circle cx="26" cy="{TITLEBAR_H // 2}" r="6" fill="#ff5f57"/>'
        f'<circle cx="46" cy="{TITLEBAR_H // 2}" r="6" fill="#febc2e"/>'
        f'<circle cx="66" cy="{TITLEBAR_H // 2}" r="6" fill="#28c840"/>'
        f'<text x="{CANVAS_W // 2}" y="{TITLEBAR_H // 2 + 5}" '
        f'text-anchor="middle" fill="{COLORS["text_dim"]}" '
        f'font-size="13.5" font-family=\'{FONT_STACK}\'>{title}</text>'
        f"</g>"
    )


def _render_statusbar(y: int, version: str, handle: str, colors: dict) -> str:
    text_y = y + 22
    return (
        f'<g class="statusbar">'
        f'<line x1="0" y1="{y}" x2="{CANVAS_W}" y2="{y}" '
        f'stroke="rgba(255,255,255,0.05)" stroke-width="1"/>'
        f'<circle cx="26" cy="{text_y - 4}" r="3" fill="{colors["green"]}"/>'
        f'<text x="40" y="{text_y}" fill="{colors["muted_soft"]}" '
        f'font-size="11.5" font-family=\'{FONT_STACK}\' letter-spacing="1.4">ONLINE</text>'
        f'<text x="120" y="{text_y}" fill="{colors["muted_soft"]}" '
        f'font-size="11.5" font-family=\'{FONT_STACK}\' letter-spacing="1.4">'
        f'{_escape_xml(version)}</text>'
        f'<text x="{CANVAS_W - 22}" y="{text_y}" text-anchor="end" '
        f'fill="{colors["muted_soft"]}" font-size="11.5" '
        f"font-family='{FONT_STACK}' letter-spacing=\"1.4\">"
        f'github.com/{_escape_xml(handle)}</text>'
        f"</g>"
    )
