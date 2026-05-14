"""SVG renderer for the 8enji dashboard.

Pure functions: no I/O, no global state. Coordinates and colors derive
from the design at readme/project/readme.html in the design handoff.
"""

from datetime import date

CANVAS_W = 1500
CANVAS_PADDING = 14

COLORS = {
    "bg_outer": "#07090d",
    "bg": "#0e1218",
    "panel_border": "rgba(148,163,184,0.10)",
    "text": "#cdd6e1",
    "text_dim": "#8b95a3",
    "muted": "#5a6473",
    "muted_soft": "#3f4753",
    "purple": "#c8a2ff",
    "green": "#b6e04f",
    "orange": "#f1c47a",
    "ts": "#5fb7ff",
    "py": "#c8a2ff",
    "go": "#b6e04f",
    "rust": "#f1c47a",
    "lua": "#ee557d",
    "other": "#ee557d",
}

FONT_STACK = '"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace'

TITLEBAR_H = 45
STATUSBAR_H = 36


def render_chrome(title_left: str, title_right: str) -> str:
    """Render the window border + titlebar. Returns a single <g> string."""
    title = f"btop — <tspan font-weight='500' fill='{COLORS['text']}'>{title_left}.{title_right}</tspan>"
    return f"""<g class="chrome">
  <rect x="0" y="0" width="{CANVAS_W}" height="100%" rx="14" ry="14" fill="{COLORS['bg']}" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
  <line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W}" y2="{TITLEBAR_H}" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
  <circle cx="26" cy="{TITLEBAR_H // 2}" r="6" fill="#ff5f57"/>
  <circle cx="46" cy="{TITLEBAR_H // 2}" r="6" fill="#febc2e"/>
  <circle cx="66" cy="{TITLEBAR_H // 2}" r="6" fill="#28c840"/>
  <text x="{CANVAS_W // 2}" y="{TITLEBAR_H // 2 + 5}" text-anchor="middle" fill="{COLORS['text_dim']}" font-size="13.5" font-family='{FONT_STACK}'>{title}</text>
</g>"""


def render_statusbar(cfg: dict, clock: str, y: int) -> str:
    """Render the bottom statusbar at vertical position `y`."""
    left_x = 22
    right_x = CANVAS_W - 22
    text_y = y + 22
    cs = COLORS["muted_soft"]
    fs = 11.5
    family = FONT_STACK
    return f"""<g class="statusbar">
  <line x1="0" y1="{y}" x2="{CANVAS_W}" y2="{y}" stroke="rgba(255,255,255,0.05)" stroke-width="1"/>
  <circle cx="{left_x + 4}" cy="{text_y - 4}" r="3" fill="{COLORS['green']}"/>
  <text x="{left_x + 16}" y="{text_y}" fill="{cs}" font-size="{fs}" font-family='{family}' letter-spacing="1.4">CPU {cfg['cpu']}</text>
  <text x="{left_x + 130}" y="{text_y}" fill="{cs}" font-size="{fs}" font-family='{family}' letter-spacing="1.4">MEM {cfg['mem']}</text>
  <text x="{left_x + 240}" y="{text_y}" fill="{cs}" font-size="{fs}" font-family='{family}' letter-spacing="1.4">NET {cfg['net']}</text>
  <text x="{right_x - 240}" y="{text_y}" fill="{cs}" font-size="{fs}" font-family='{family}' letter-spacing="1.4">{cfg['version']}</text>
  <text x="{right_x - 130}" y="{text_y}" fill="{cs}" font-size="{fs}" font-family='{family}' letter-spacing="1.4">UTF-8</text>
  <text x="{right_x - 70}" y="{text_y}" fill="{cs}" font-size="{fs}" font-family='{family}' letter-spacing="1.4">NOR</text>
  <text x="{right_x}" y="{text_y}" text-anchor="end" fill="{cs}" font-size="{fs}" font-family='{family}' letter-spacing="1.4">{clock}</text>
</g>"""


def render_panel_frame(x: int, y: int, w: int, h: int, label: str, right: str = "") -> str:
    """Render an empty panel: rounded border + heading row.

    Header text uses uppercase tracked letter-spacing per the design.
    """
    head_y = y + 28
    body_x = x + 22
    return f"""<g class="panel" data-label="{label}">
  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" ry="9"
        fill="rgba(255,255,255,0.012)" stroke="{COLORS['panel_border']}" stroke-width="1"/>
  <text x="{body_x}" y="{head_y}" fill="{COLORS['muted']}" font-size="11.5"
        font-family='{FONT_STACK}' font-weight="600" letter-spacing="1.6"
        text-transform="uppercase">{label.upper()}</text>
  <text x="{x + w - 22}" y="{head_y}" text-anchor="end" fill="{COLORS['muted_soft']}"
        font-size="11.5" font-family='{FONT_STACK}' font-weight="500"
        letter-spacing="1.4" text-transform="uppercase">{right}</text>
</g>"""


def _format_uptime(uptime_from: str, today: date) -> str:
    """Convert ISO date string to `Ny Md` since that date."""
    start = date.fromisoformat(uptime_from)
    delta_days = (today - start).days
    years = delta_days // 365
    days = delta_days % 365
    return f"{years}y {days}d"


def _escape_xml(s: str) -> str:
    """Minimal XML escape for text content."""
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_me_panel(cfg: dict, x: int, y: int, w: int, h: int, today: date) -> str:
    frame = render_panel_frame(x, y, w, h, "me", "/etc/8enji.png")

    # ASCII portrait — fixed-width font, 8px, line-height 1.05
    ascii_lines = cfg["ascii_art"].rstrip("\n").split("\n")
    ascii_x = x + 22
    ascii_y = y + 56
    line_height = 8 * 1.05
    ascii_tspans = "".join(
        f'<tspan x="{ascii_x}" dy="{0 if i == 0 else line_height}">{_escape_xml(line)}</tspan>'
        for i, line in enumerate(ascii_lines)
    )
    ascii_block = (
        f'<text font-family=\'{FONT_STACK}\' font-size="8" fill="{COLORS["text_dim"]}" '
        f'xml:space="preserve" font-weight="500" y="{ascii_y}">{ascii_tspans}</text>'
    )

    # Sysinfo table — purple keys, light values
    me = cfg["me"]
    sys_rows = [
        ("host", f'{cfg["handle"]}<tspan fill="{COLORS["muted"]}">@</tspan>{cfg["machine"]}'),
        ("os", me["os"]),
        ("shell", me["shell"]),
        ("editor", me["editor"]),
        ("wm", me["wm"]),
        ("theme", me["theme"]),
        ("uptime", _format_uptime(me["uptime_from"], today)),
    ]
    sys_x_key = x + 380
    sys_x_val = sys_x_key + 90
    sys_y_start = y + h // 2 - (len(sys_rows) * 22) // 2 + 8
    sys_lines = []
    for i, (k, v) in enumerate(sys_rows):
        row_y = sys_y_start + i * 22
        sys_lines.append(
            f'<text x="{sys_x_key}" y="{row_y}" fill="{COLORS["purple"]}" font-size="13" font-family=\'{FONT_STACK}\'>{k}</text>'
        )
        # value may contain inline <tspan> for the host row
        sys_lines.append(
            f'<text x="{sys_x_val}" y="{row_y}" fill="{COLORS["text"]}" font-size="13" font-family=\'{FONT_STACK}\'>{v}</text>'
        )
    sysinfo = "\n".join(sys_lines)

    # Footer — handle · website ……… online
    footer_y = y + h - 22
    footer_top = footer_y - 14
    footer = (
        f'<line x1="{x + 22}" y1="{footer_top}" x2="{x + w - 22}" y2="{footer_top}" '
        f'stroke="rgba(148,163,184,0.08)" stroke-width="1" stroke-dasharray="3 3"/>'
        f'<text x="{x + 22}" y="{footer_y}" fill="{COLORS["muted"]}" font-size="11.5" '
        f'font-family=\'{FONT_STACK}\' letter-spacing="1.8" text-transform="uppercase">'
        f'{cfg["handle"]} <tspan fill="{COLORS["muted_soft"]}">·</tspan> {cfg["website"]}</text>'
        f'<text x="{x + w - 22}" y="{footer_y}" text-anchor="end" fill="{COLORS["green"]}" '
        f'font-size="11.5" font-family=\'{FONT_STACK}\' letter-spacing="1.8" text-transform="uppercase">'
        f'// online</text>'
    )

    return frame + ascii_block + sysinfo + footer


LANG_COLOR_MAP = {
    # Design palette
    "typescript":  COLORS["ts"],
    "javascript":  "#f1e05a",
    "python":      COLORS["py"],
    "go":          COLORS["go"],
    "rust":        COLORS["rust"],
    "lua":         COLORS["lua"],
    # Extended palette — vibrant colors tuned for dark theme
    "java":        "#f89820",
    "kotlin":      "#a97bff",
    "swift":       "#ff7e3b",
    "objective-c": "#438eff",
    "ruby":        "#cc342d",
    "php":         "#787cb5",
    "html":        "#e44d26",
    "css":         "#5fb7ff",
    "scss":        "#cc6699",
    "sass":        "#cc6699",
    "shell":       "#89e051",
    "bash":        "#89e051",
    "zsh":         "#89e051",
    "powershell":  "#3a8fb7",
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
    "erlang":      "#b83998",
    "perl":        "#0fc4dc",
    "ocaml":       "#ee8e30",
    "clojure":     "#b6e04f",
    "elm":         "#7fb8d4",
    "matlab":      "#e16737",
    "sql":         "#e38c00",
    "graphql":     "#e535ab",
    "tex":         "#82b541",
    "latex":       "#82b541",
    "markdown":    COLORS["text_dim"],
    "dockerfile":  "#0db7ed",
    "makefile":    "#b6e04f",
    "cmake":       "#e76f51",
    "yaml":        "#e5c07b",
    "json":        "#cdd6e1",
    "toml":        "#9c4221",
    "vim script":  "#019733",
    "lua-luvit":   COLORS["lua"],
    "fish":        "#4eada4",
    "nix":         "#7e7eff",
    "zig":         "#ec915c",
    "v":           "#5d87bf",
    "crystal":     "#cdd6e1",
    "julia":       "#a270ba",
    "wasm":        "#04133b",
    "assembly":    "#6e4c13",
}


def _lang_color(name: str) -> str:
    return LANG_COLOR_MAP.get(name.lower(), COLORS["other"])


def render_languages_panel(languages: list[tuple[str, float]], x: int, y: int, w: int, h: int) -> str:
    frame = render_panel_frame(x, y, w, h, "languages", "last 12mo")

    # Layout: name(88) | bar(flex) | pct(44), gap 14, padding 22
    body_x = x + 22
    body_w = w - 44
    name_w = 88
    pct_w = 44
    gap = 14
    bar_x = body_x + name_w + gap
    bar_w = body_w - name_w - pct_w - 2 * gap
    pct_x = body_x + body_w  # right-aligned

    # 6 rows evenly distributed inside body height (h - header - bottom padding)
    rows_top = y + 56
    rows_bottom = y + h - 24
    row_count = max(len(languages), 1)
    row_h = (rows_bottom - rows_top) / row_count

    out = [frame]
    for i, (name, pct) in enumerate(languages):
        cy = rows_top + i * row_h + row_h / 2
        text_y = cy + 5
        bar_y = cy - 7
        color = _lang_color(name)
        fill_w = max(0, int(bar_w * (pct / 100)))
        out.append(
            f'<text x="{body_x}" y="{text_y}" fill="{COLORS["text"]}" font-size="13" '
            f'font-family=\'{FONT_STACK}\'>{name}</text>'
        )
        # Trough (faint solid + diagonal hatch via pattern reference)
        out.append(
            f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="14" rx="3" ry="3" '
            f'fill="rgba(255,255,255,0.03)"/>'
        )
        out.append(
            f'<rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="14" rx="3" ry="3" '
            f'fill="{color}" fill-opacity="0.22" mask="url(#hatch-mask)"/>'
        )
        # Fill
        out.append(
            f'<rect x="{bar_x}" y="{bar_y}" width="{fill_w}" height="14" rx="3" ry="3" '
            f'fill="{color}"/>'
        )
        # Percentage
        out.append(
            f'<text x="{pct_x}" y="{text_y}" text-anchor="end" fill="{COLORS["text_dim"]}" '
            f'font-size="13" font-family=\'{FONT_STACK}\' font-variant-numeric="tabular-nums">'
            f'{int(round(pct))}%</text>'
        )

    return "".join(out)


def render_activity_panel(
    activity: list[int],
    peak: int,
    streak_days: int,
    avg: float,
    x: int,
    y: int,
    w: int,
    h: int,
) -> str:
    frame = render_panel_frame(x, y, w, h, "activity", f"peak {peak}/day · streak {streak_days}d")

    body_x = x + 22
    body_w = w - 44
    sub_y = y + 60
    chart_top = y + 80
    chart_bottom = y + h - 48
    chart_h = chart_bottom - chart_top
    axis_y = chart_bottom + 18

    # Sub-row: "commits/day · last 60 days" green | "avg 14.3" muted
    sub = (
        f'<text x="{body_x}" y="{sub_y}" fill="{COLORS["green"]}" font-size="13" '
        f'font-family=\'{FONT_STACK}\'>commits/day · last 60 days</text>'
        f'<text x="{x + w - 22}" y="{sub_y}" text-anchor="end" fill="{COLORS["muted"]}" '
        f'font-size="11.5" font-family=\'{FONT_STACK}\' letter-spacing="1.1">avg {avg:.1f}</text>'
    )

    # Bars
    n = max(len(activity), 1)
    gap = 4
    bar_w = (body_w - gap * (n - 1)) / n
    max_v = max(activity) if activity else 1
    bars = []
    for i, v in enumerate(activity):
        pct = max(0.10, v / max_v)  # min 10% so empty days still register
        bh = chart_h * pct
        bx = body_x + i * (bar_w + gap)
        by = chart_bottom - bh
        bars.append(
            f'<rect class="bar-bar" x="{bx:.2f}" y="{by:.2f}" width="{bar_w:.2f}" '
            f'height="{bh:.2f}" rx="2" ry="2" fill="{COLORS["green"]}"/>'
        )

    # Axis line + labels
    labels_y = axis_y + 10
    axis_line = (
        f'<line x1="{body_x}" y1="{axis_y}" x2="{x + w - 22}" y2="{axis_y}" '
        f'stroke="rgba(148,163,184,0.08)" stroke-width="1" stroke-dasharray="3 3"/>'
    )
    label_positions = [
        (body_x, "60d", "start"),
        (body_x + body_w * 0.25, "45d", "middle"),
        (body_x + body_w * 0.50, "30d", "middle"),
        (body_x + body_w * 0.75, "15d", "middle"),
        (body_x + body_w, "today", "end"),
    ]
    labels = "".join(
        f'<text x="{lx:.2f}" y="{labels_y}" text-anchor="{anchor}" fill="{COLORS["muted_soft"]}" '
        f'font-size="11" font-family=\'{FONT_STACK}\' letter-spacing="0.88" '
        f'text-transform="uppercase">{txt}</text>'
        for lx, txt, anchor in label_positions
    )

    return frame + sub + "".join(bars) + axis_line + labels


def format_compact(n: int) -> str:
    return f"{n:,}"


def format_loc(total_bytes: int) -> str:
    lines = total_bytes // 50
    return f"{lines // 1000}k"


def render_stats_panel(stats: dict, x: int, y: int, w: int, h: int) -> str:
    frame = render_panel_frame(x, y, w, h, "stats", "● LIVE")

    body_x = x + 22
    body_w = w - 44
    row_y = y + 60
    row_h = 26

    rows = [
        ("repos", str(stats["repos"]), False),
        ("stars", str(stats["stars"]), True),
        ("followers", str(stats["followers"]), False),
        ("commits", format_compact(stats["commits"]), False),
        ("loc", format_loc(stats["loc_bytes"]), False),
    ]

    out = [frame]
    for i, (k, v, has_star) in enumerate(rows):
        ry = row_y + i * row_h
        v_text = v + (f'<tspan fill="{COLORS["orange"]}" dx="6">★</tspan>' if has_star else "")
        out.append(
            f'<text x="{body_x}" y="{ry}" fill="{COLORS["text"]}" font-size="13" '
            f'font-family=\'{FONT_STACK}\'>{k}</text>'
        )
        out.append(
            f'<text x="{body_x + body_w}" y="{ry}" text-anchor="end" fill="{COLORS["text"]}" '
            f'font-size="13" font-family=\'{FONT_STACK}\' font-variant-numeric="tabular-nums">'
            f'{v_text}</text>'
        )
        if i < len(rows) - 1:
            out.append(
                f'<line x1="{body_x}" y1="{ry + 8}" x2="{body_x + body_w}" y2="{ry + 8}" '
                f'stroke="rgba(148,163,184,0.06)" stroke-width="1" stroke-dasharray="1 4"/>'
            )

    # Top repos header
    top_head_y = row_y + len(rows) * row_h + 18
    out.append(
        f'<line x1="{body_x}" y1="{top_head_y - 14}" x2="{body_x + body_w}" y2="{top_head_y - 14}" '
        f'stroke="rgba(148,163,184,0.10)" stroke-width="1" stroke-dasharray="3 3"/>'
    )
    out.append(
        f'<text x="{body_x}" y="{top_head_y}" fill="{COLORS["muted"]}" font-size="11.5" '
        f'font-family=\'{FONT_STACK}\' letter-spacing="1.6" text-transform="uppercase">top repos</text>'
    )
    out.append(
        f'<text x="{body_x + body_w}" y="{top_head_y}" text-anchor="end" fill="{COLORS["muted_soft"]}" '
        f'font-size="11.5" font-family=\'{FONT_STACK}\' font-weight="500" letter-spacing="1.4" '
        f'text-transform="uppercase">by ★</text>'
    )

    # Top repo rows
    for i, repo in enumerate(stats["top_repos"][:3]):
        ry = top_head_y + 22 + i * 22
        out.append(
            f'<text x="{body_x}" y="{ry}" fill="{COLORS["text"]}" font-size="13" '
            f'font-family=\'{FONT_STACK}\'>{_escape_xml(repo["name"])}</text>'
        )
        out.append(
            f'<text x="{body_x + body_w - 80}" y="{ry}" text-anchor="end" '
            f'fill="{COLORS["text_dim"]}" font-size="12" font-family=\'{FONT_STACK}\'>'
            f'{_escape_xml(repo["language"])}</text>'
        )
        out.append(
            f'<text x="{body_x + body_w}" y="{ry}" text-anchor="end" fill="{COLORS["orange"]}" '
            f'font-size="13" font-family=\'{FONT_STACK}\' font-variant-numeric="tabular-nums">'
            f'★ {repo["stars"]}</text>'
        )

    return "".join(out)


def render_now_panel(cfg: dict, x: int, y: int, w: int, h: int) -> str:
    frame = render_panel_frame(x, y, w, h, "now", "/etc/8enji.conf")

    body_x = x + 22
    body_w = w - 44
    col_gap = 40
    col_w = (body_w - col_gap) // 2
    col1_x = body_x
    col2_x = body_x + col_w + col_gap
    key_w = 110

    now = cfg["now"]
    rows = [
        (col1_x, "building", now["building"]),
        (col2_x, "learning", now["learning"]),
        (col1_x, "listening", now["listening"]),
        (col2_x, "reach", now["reach"]),
    ]

    row_y_top = y + 70
    row_h = 30

    out = [frame]
    # First row pair (building / learning)
    for cx, k, v in rows[:2]:
        out.append(
            f'<text x="{cx}" y="{row_y_top}" fill="{COLORS["purple"]}" font-size="14" '
            f'font-family=\'{FONT_STACK}\'>{k}</text>'
        )
        out.append(
            f'<text x="{cx + key_w}" y="{row_y_top}" fill="{COLORS["text"]}" font-size="14" '
            f'font-family=\'{FONT_STACK}\'>{_escape_xml(v)}</text>'
        )
    # Dotted dividers below first row
    for cx in (col1_x, col2_x):
        out.append(
            f'<line x1="{cx}" y1="{row_y_top + 12}" x2="{cx + col_w}" y2="{row_y_top + 12}" '
            f'stroke="rgba(148,163,184,0.06)" stroke-width="1" stroke-dasharray="1 4"/>'
        )

    # Second row pair (listening / reach)
    for cx, k, v in rows[2:]:
        ry = row_y_top + row_h
        out.append(
            f'<text x="{cx}" y="{ry}" fill="{COLORS["purple"]}" font-size="14" '
            f'font-family=\'{FONT_STACK}\'>{k}</text>'
        )
        out.append(
            f'<text x="{cx + key_w}" y="{ry}" fill="{COLORS["text"]}" font-size="14" '
            f'font-family=\'{FONT_STACK}\'>{_escape_xml(v)}</text>'
        )

    return "".join(out)


def render_defs() -> str:
    """SVG <defs> block: shared patterns/masks. Referenced by panels."""
    return """<defs>
  <pattern id="hatch" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(135)">
    <line x1="0" y1="0" x2="0" y2="12" stroke="white" stroke-width="6"/>
  </pattern>
  <mask id="hatch-mask">
    <rect x="0" y="0" width="100%" height="100%" fill="url(#hatch)"/>
  </mask>
</defs>"""


CANVAS_H = 1024


def render(config: dict, data: dict, timestamp) -> str:
    """Render the full dashboard SVG document.

    `timestamp` is a datetime; we use its UTC time and date.
    """
    today = timestamp.date()
    clock = timestamp.strftime("%H:%M:%S")

    # Grid layout
    pad = CANVAS_PADDING
    grid_top = TITLEBAR_H + pad
    col1_x = pad
    col1_w = 678
    col2_x = col1_x + col1_w + pad
    col2_w = 780

    row1_h = 426
    row1_y = grid_top
    row2_h = 354
    row2_y = row1_y + row1_h + pad
    row3_h = 106
    row3_y = row2_y + row2_h + pad
    full_w = col1_w + pad + col2_w

    statusbar_y = row3_y + row3_h + pad

    me = render_me_panel(config, col1_x, row1_y, col1_w, row1_h, today)
    langs = render_languages_panel(
        [tuple(l) for l in data["languages"]], col2_x, row1_y, col2_w, row1_h
    )
    activity = render_activity_panel(
        data["activity"], data["activity_peak"], data["activity_streak"],
        data["activity_avg"], col1_x, row2_y, col1_w, row2_h,
    )
    stats_dict = {
        "repos": data["public_repos"],
        "stars": data["total_stars"],
        "followers": data["followers"],
        "commits": data["total_commits"],
        "loc_bytes": data["total_loc_bytes"],
        "top_repos": data["top_repos"],
    }
    stats = render_stats_panel(stats_dict, col2_x, row2_y, col2_w, row2_h)
    now = render_now_panel(config, col1_x, row3_y, full_w, row3_h)
    statusbar = render_statusbar(config["statusbar"], clock, statusbar_y)
    chrome = render_chrome(title_left=config["handle"], title_right=config["machine"])
    defs = render_defs()

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {CANVAS_W} {CANVAS_H}"
     width="{CANVAS_W}" height="{CANVAS_H}" font-family='{FONT_STACK}'>
  <rect width="100%" height="100%" fill="{COLORS['bg_outer']}"/>
  {defs}
  {chrome}
  {me}
  {langs}
  {activity}
  {stats}
  {now}
  {statusbar}
</svg>"""
