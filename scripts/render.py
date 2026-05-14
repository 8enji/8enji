"""SVG renderer for the 8enji dashboard.

Pure functions: no I/O, no global state. Coordinates and colors derive
from the design at readme/project/readme.html in the design handoff.
"""

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
