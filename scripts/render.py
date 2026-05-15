"""
scripts/render.py — pure SVG renderer for the 8enji dashboard.

No I/O, no network. Takes a parsed config + a fetched GitHub data dict and
returns an SVG string ready to be written to dashboard.svg.

The output mirrors readme-minimal.html: a macOS-terminal-shaped window with
an ASCII portrait on the left and a neofetch-style info column on the right.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from html import escape
from typing import Any, Mapping

# ── canvas ───────────────────────────────────────────────────────────────
CANVAS_W = 1280  # fixed; matches readme-minimal.html .window width

# ── palette ──────────────────────────────────────────────────────────────
BG          = "#12161e"
BORDER      = "rgba(255,255,255,0.06)"
TITLE_LINE  = "rgba(255,255,255,0.05)"
TEXT        = "#cdd6e1"
TEXT_DIM    = "#8b95a3"
MUTED       = "#5a6473"
MUTED_SOFT  = "#3f4753"
GREEN       = "#b6e04f"
PURPLE      = "#c8a2ff"
ORANGE      = "#f1c47a"
PINK        = "#ee557d"

LANG_DOT_COLORS: dict[str, str] = {
    "typescript": "#5fb7ff",
    "javascript": "#5fb7ff",
    "python":     "#c8a2ff",
    "go":         "#b6e04f",
    "rust":       "#f1c47a",
    "lua":        "#ee557d",
    "c":          "#cdd6e1",
    "c++":        "#cdd6e1",
    "shell":      "#b6e04f",
    "html":       "#ee557d",
    "css":        "#5fb7ff",
}
LANG_DOT_FALLBACK = MUTED

MONO_STACK = (
    "'JetBrains Mono', ui-monospace, 'SF Mono', "
    "SFMono-Regular, Menlo, Consolas, monospace"
)

# ── tweaks ───────────────────────────────────────────────────────────────
@dataclass
class Tweaks:
    ascii_size: int = 12
    ascii_color: str = TEXT_DIM
    accent: str = GREEN
    font_size: int = 19
    gap: int = 44
    pad_x: int = 88
    pad_y: int = 44
    show_stats: bool = True
    show_languages: bool = True
    show_now: bool = True
    show_palette: bool = False
    show_statusbar: bool = False
    show_rule: bool = False

    @classmethod
    def from_config(cls, raw: Mapping[str, Any] | None) -> "Tweaks":
        if not raw:
            return cls()
        known = {f.name for f in fields(cls)}
        cleaned = {k: v for k, v in raw.items() if k in known}
        return cls(**cleaned)


# ── helpers ──────────────────────────────────────────────────────────────
def _e(s: Any) -> str:
    """XML-escape."""
    return escape(str(s), quote=True)


def _dedent_ascii(s: str) -> str:
    """Strip the shared left-indent so the figure sits flush at column 0."""
    lines = s.splitlines()
    indents = [len(l) - len(l.lstrip(" ")) for l in lines if l.strip()]
    if not indents:
        return s
    n = min(indents)
    return "\n".join(l[n:] if len(l) >= n else l for l in lines)


def _font(size: int) -> str:
    return f' font-size="{size}" font-family="{MONO_STACK}"'


def _text(
    x: float, y: float, fill: str, size: int, content: str,
    weight: str = "", anchor: str = "",
) -> str:
    extra = ""
    if weight:
        extra += f' font-weight="{weight}"'
    if anchor:
        extra += f' text-anchor="{anchor}"'
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" fill="{fill}"'
        f'{_font(size)}{extra}>{content}</text>'
    )


def _colorize_value(v: str) -> str:
    """Dim · separators and (parentheticals) inside KV values."""
    out = _e(v)
    out = out.replace("·", f'<tspan fill="{MUTED}">·</tspan>')
    out = re.sub(
        r"\(([^)]+)\)",
        lambda m: f'<tspan fill="{MUTED}">({_e(m.group(1))})</tspan>',
        out,
    )
    return out


# ── height estimation (mirrors info column layout) ───────────────────────
def _estimate_info_height(
    tw: Tweaks, kv_rows: int, stat_rows: int, now_rows: int,
) -> dict[str, float | int | None]:
    """Returns y-offsets for each block relative to the info-column top."""
    fs = tw.font_size
    prompt_fs  = round(fs * 1.14)
    section_fs = round(fs * 0.82)
    lang_fs    = round(fs * 0.93)
    kv_row_h   = fs + 4
    stat_row_h = fs + 7
    block_gap  = 22

    y = 0.0
    prompt_baseline = y + prompt_fs
    y += prompt_fs + 4

    rule_y: float | None = None
    if tw.show_rule:
        rule_y = y + section_fs * 0.5
        y += section_fs + 12

    kv1_top = y
    y += kv_rows * kv_row_h + block_gap

    stats_title_y = stats_top = None
    if tw.show_stats and stat_rows:
        stats_title_y = y + section_fs
        y += section_fs + 10
        stats_top = y
        rows = -(-stat_rows // 2)  # ceil
        y += rows * stat_row_h + block_gap

    langs_title_y = langs_row_y = None
    if tw.show_languages:
        langs_title_y = y + section_fs
        y += section_fs + 10
        langs_row_y = y + lang_fs
        y += lang_fs + 6 + block_gap

    now_title_y = now_top = None
    if tw.show_now and now_rows:
        now_title_y = y + section_fs
        y += section_fs + 10
        now_top = y
        y += now_rows * kv_row_h

    return dict(
        prompt_fs=prompt_fs, section_fs=section_fs, lang_fs=lang_fs,
        kv_row_h=kv_row_h, stat_row_h=stat_row_h,
        prompt_baseline=prompt_baseline,
        rule_y=rule_y,
        kv1_top=kv1_top,
        stats_title_y=stats_title_y, stats_top=stats_top,
        langs_title_y=langs_title_y, langs_row_y=langs_row_y,
        now_title_y=now_title_y, now_top=now_top,
        total_height=y,
    )


# ── data assembly ────────────────────────────────────────────────────────
def _humanize_loc(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}m"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


def _build_kv1(config: Mapping[str, Any], data: Mapping[str, Any]) -> list[tuple[str, str]]:
    me = config.get("me", {})
    rows: list[tuple[str, str]] = []
    for key in ("os", "host", "shell", "editor", "theme"):
        if key in me:
            rows.append((key, str(me[key])))
    if "uptime" in data:
        rows.append(("uptime", str(data["uptime"])))
    return rows


def _build_stats(data: Mapping[str, Any]) -> list[tuple[str, str]]:
    return [
        ("repos",     f'{data.get("repos", 0)}'),
        ("stars",     f'{data.get("stars", 0)} ★'),
        ("followers", f'{data.get("followers", 0)}'),
        ("commits",   f'{data.get("commits", 0):,}'),
        ("streak",    f'{data.get("streak", 0)}d'),
        ("loc",       _humanize_loc(data.get("loc", 0))),
    ]


def _build_langs(data: Mapping[str, Any]) -> list[tuple[str, str, str]]:
    """Top 3 + 'other'."""
    raw = data.get("languages", {})
    if not raw:
        return []
    total = sum(raw.values()) or 1
    items = sorted(raw.items(), key=lambda kv: -kv[1])
    top = items[:3]
    rest = sum(v for _, v in items[3:])
    out: list[tuple[str, str, str]] = []
    for name, count in top:
        pct = round(count / total * 100)
        color = LANG_DOT_COLORS.get(name.lower(), LANG_DOT_FALLBACK)
        out.append((name.lower(), f"{pct}%", color))
    if rest > 0:
        pct = round(rest / total * 100)
        out.append(("other", f"{pct}%", LANG_DOT_FALLBACK))
    return out


def _build_now(config: Mapping[str, Any]) -> list[tuple[str, str]]:
    now = config.get("now", {})
    keys = ("building", "learning", "listening", "reach")
    return [(k, str(now[k])) for k in keys if k in now]


# ── renderer ─────────────────────────────────────────────────────────────
def render(config: Mapping[str, Any], data: Mapping[str, Any]) -> str:
    tw = Tweaks.from_config(config.get("tweaks"))

    ascii_art = _dedent_ascii(config.get("ascii_art", ""))
    ascii_lines = ascii_art.splitlines() or [""]
    kv1   = _build_kv1(config, data)
    stats = _build_stats(data) if tw.show_stats else []
    langs = _build_langs(data) if tw.show_languages else []
    nowkv = _build_now(config) if tw.show_now else []

    # geometry
    title_h = 50
    char_w  = tw.ascii_size * 0.6
    ascii_w = max((int(len(l) * char_w) for l in ascii_lines), default=0)
    ascii_h = len(ascii_lines) * tw.ascii_size

    info_x = tw.pad_x + ascii_w + tw.gap
    m = _estimate_info_height(tw, len(kv1), len(stats), len(nowkv))
    info_h = m["total_height"]

    body_h = max(ascii_h, info_h) + tw.pad_y * 2 + 4
    canvas_h = int(title_h + body_h)

    info_top  = title_h + tw.pad_y + max(0, (ascii_h - info_h) / 2)
    ascii_top = title_h + tw.pad_y + max(0, (info_h - ascii_h) / 2)

    def y_at(rel: float) -> float:
        return info_top + rel

    parts: list[str] = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {CANVAS_W} {canvas_h}" '
        f'width="{CANVAS_W}" height="{canvas_h}" '
        f'role="img" aria-label="8enji dashboard">'
    )
    parts.append(
        '<defs>'
        f'<clipPath id="clip"><rect x="0" y="0" width="{CANVAS_W}" '
        f'height="{canvas_h}" rx="14" ry="14"/></clipPath>'
        '</defs>'
        '<g clip-path="url(#clip)">'
        f'<rect x="0" y="0" width="{CANVAS_W}" height="{canvas_h}" fill="{BG}"/>'
    )

    # ── titlebar ──
    parts.append(
        f'<line x1="0" y1="{title_h}" x2="{CANVAS_W}" y2="{title_h}" stroke="{TITLE_LINE}"/>'
        f'<circle cx="22" cy="{title_h / 2}" r="6" fill="#ff5f57"/>'
        f'<circle cx="42" cy="{title_h / 2}" r="6" fill="#febc2e"/>'
        f'<circle cx="62" cy="{title_h / 2}" r="6" fill="#28c840"/>'
    )
    title_text = config.get("title", "8enji — -zsh — 96×32")
    parts.append(_text(
        CANVAS_W / 2, title_h / 2 + 5, TEXT_DIM, 14,
        _e(title_text), anchor="middle",
    ))

    # ── ascii portrait ──
    tspans = "".join(
        f'<tspan x="{tw.pad_x}" dy="{0 if i == 0 else tw.ascii_size}" '
        f'xml:space="preserve">{_e(line)}</tspan>'
        for i, line in enumerate(ascii_lines)
    )
    parts.append(
        f'<text fill="{tw.ascii_color}"{_font(tw.ascii_size)} '
        f'x="{tw.pad_x}" y="{ascii_top + tw.ascii_size:.1f}" '
        f'font-weight="500" xml:space="preserve">{tspans}</text>'
    )

    # ── prompt ──
    handle = config.get("me", {}).get("handle", "8enji")
    host   = config.get("me", {}).get("host_short", "dashboard")
    parts.append(
        f'<text x="{info_x}" y="{y_at(m["prompt_baseline"]):.1f}"'
        f'{_font(m["prompt_fs"])}>'
        f'<tspan fill="{TEXT}" font-weight="500">{_e(handle)}</tspan>'
        f'<tspan fill="{TEXT_DIM}">@</tspan>'
        f'<tspan fill="{TEXT}" font-weight="500">{_e(host)}</tspan>'
        '</text>'
    )

    # ── optional rule under prompt ──
    if tw.show_rule and m["rule_y"] is not None:
        rule_w = 240
        parts.append(
            f'<line x1="{info_x}" y1="{y_at(m["rule_y"]):.1f}" '
            f'x2="{info_x + rule_w}" y2="{y_at(m["rule_y"]):.1f}" '
            f'stroke="{MUTED_SOFT}" stroke-width="1"/>'
        )

    # ── kv1 ──
    kv_key_w = 96
    for i, (k, v) in enumerate(kv1):
        y = y_at(m["kv1_top"] + i * m["kv_row_h"] + tw.font_size)
        parts.append(_text(info_x, y, PURPLE, tw.font_size, _e(k)))
        parts.append(_text(info_x + kv_key_w, y, TEXT, tw.font_size, _colorize_value(v)))

    # ── stats ──
    if tw.show_stats and stats:
        parts.append(_text(
            info_x, y_at(m["stats_title_y"]),
            MUTED, m["section_fs"], _e("STATS"), weight="600",
        ))
        stat_col_w   = 280
        stat_col_gap = 32
        for i, (k, v) in enumerate(stats):
            col = i % 2
            row = i // 2
            x = info_x + col * (stat_col_w + stat_col_gap)
            y = y_at(m["stats_top"] + row * m["stat_row_h"] + tw.font_size)
            parts.append(_text(x, y, TEXT_DIM, tw.font_size, _e(k)))
            v_marked = _e(v).replace("★", f'<tspan fill="{ORANGE}">★</tspan>')
            parts.append(_text(x + stat_col_w, y, TEXT, tw.font_size, v_marked, anchor="end"))
            parts.append(
                f'<line x1="{x}" y1="{y + 4:.1f}" '
                f'x2="{x + stat_col_w}" y2="{y + 4:.1f}" '
                f'stroke="{MUTED_SOFT}" stroke-opacity="0.35" '
                f'stroke-width="1" stroke-dasharray="1 3"/>'
            )

    # ── languages ──
    if tw.show_languages and langs:
        parts.append(_text(
            info_x, y_at(m["langs_title_y"]),
            MUTED, m["section_fs"], _e("LANGUAGES · LAST 12MO"), weight="600",
        ))
        cursor = info_x
        for (name, pct, color) in langs:
            dot_size = 10
            dot_y = y_at(m["langs_row_y"]) - m["lang_fs"] * 0.55
            parts.append(
                f'<rect x="{cursor}" y="{dot_y:.1f}" '
                f'width="{dot_size}" height="{dot_size}" rx="2" fill="{color}"/>'
            )
            cursor += dot_size + 8
            label = f'{_e(name)} <tspan fill="{TEXT_DIM}">{_e(pct)}</tspan>'
            parts.append(_text(cursor, y_at(m["langs_row_y"]),
                               TEXT, m["lang_fs"], label))
            cursor += len(name + " " + pct) * m["lang_fs"] * 0.6 + 22

    # ── now ──
    if tw.show_now and nowkv:
        parts.append(_text(
            info_x, y_at(m["now_title_y"]),
            MUTED, m["section_fs"], _e("NOW"), weight="600",
        ))
        for i, (k, v) in enumerate(nowkv):
            y = y_at(m["now_top"] + i * m["kv_row_h"] + tw.font_size)
            parts.append(_text(info_x, y, PURPLE, tw.font_size, _e(k)))
            parts.append(_text(info_x + kv_key_w, y, TEXT, tw.font_size, _colorize_value(v)))

    # ── palette swatches (optional) ──
    if tw.show_palette:
        palette_y = canvas_h - tw.pad_y - 14
        sw_w, sw_h = 28, 14
        swatches = ["#1a1f29", PINK, tw.accent, ORANGE,
                    "#5fb7ff", PURPLE, "#5fd9c8", TEXT]
        for i, c in enumerate(swatches):
            parts.append(
                f'<rect x="{info_x + i * sw_w}" y="{palette_y}" '
                f'width="{sw_w}" height="{sw_h}" fill="{c}"/>'
            )

    # ── status bar (optional) ──
    if tw.show_statusbar:
        sb_h = 32
        sb_y = canvas_h - sb_h
        parts.append(
            f'<line x1="0" y1="{sb_y}" x2="{CANVAS_W}" y2="{sb_y}" stroke="{TITLE_LINE}"/>'
            f'<circle cx="22" cy="{sb_y + sb_h / 2}" r="3" fill="{tw.accent}"/>'
        )
        parts.append(_text(
            34, sb_y + sb_h / 2 + 4, MUTED_SOFT, 11,
            _e("ONLINE  ·  V2.6.0"), weight="600",
        ))
        parts.append(_text(
            CANVAS_W - 22, sb_y + sb_h / 2 + 4, MUTED_SOFT, 11,
            _e(config.get("me", {}).get("github_url", "GITHUB.COM/8ENJI")),
            weight="600", anchor="end",
        ))

    # subtle outer border
    parts.append(
        f'<rect x="0.5" y="0.5" width="{CANVAS_W - 1}" height="{canvas_h - 1}" '
        f'rx="13.5" ry="13.5" fill="none" stroke="{BORDER}"/>'
    )
    parts.append("</g></svg>")
    return "".join(parts)
