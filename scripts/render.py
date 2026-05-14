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
