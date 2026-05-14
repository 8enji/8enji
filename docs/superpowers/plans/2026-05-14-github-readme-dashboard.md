# GitHub README Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a live, auto-refreshing btop-style terminal dashboard SVG for the `8enji/8enji` GitHub profile README, driven by GitHub API data and a hand-edited `config.yml`.

**Architecture:** A Python script (`scripts/generate.py`) fetches stats from the GitHub REST + GraphQL API and reads personal config from `config.yml`, then a pure `render(config, data, timestamp) -> str` function emits an SVG matching the design exactly. A GitHub Actions workflow runs the script every 6 hours and on push, committing the regenerated `dashboard.svg` only when its contents change. `README.md` embeds the SVG via a single image tag.

**Tech Stack:** Python 3.12, `requests` (REST + GraphQL POSTs), `PyYAML` (config parsing), `pytest` + `responses` (tests). No build step, no JS, no font embedding. GitHub Actions for scheduling.

**Reference design:** the design HTML lives at `/tmp/design-preview/readme/project/readme.html` (unpacked from the Anthropic design handoff bundle). Use it as the visual reference for colors, layout, and panel structure. The spec at [docs/superpowers/specs/2026-05-14-github-readme-dashboard-design.md](docs/superpowers/specs/2026-05-14-github-readme-dashboard-design.md) is the authoritative source of behavior.

---

### Task 1: Bootstrap project structure

**Files:**
- Create: `scripts/requirements.txt`
- Create: `scripts/requirements-dev.txt`
- Create: `scripts/__init__.py` (empty)
- Create: `scripts/tests/__init__.py` (empty)
- Create: `scripts/tests/fixtures/.gitkeep` (empty)
- Create: `.gitignore`

- [ ] **Step 1: Create runtime requirements**

Write `scripts/requirements.txt`:
```
requests==2.32.3
PyYAML==6.0.2
```

- [ ] **Step 2: Create dev requirements**

Write `scripts/requirements-dev.txt`:
```
-r requirements.txt
pytest==8.3.3
responses==0.25.3
```

- [ ] **Step 3: Create empty package markers**

Write empty files:
- `scripts/__init__.py`
- `scripts/tests/__init__.py`
- `scripts/tests/fixtures/.gitkeep`

- [ ] **Step 4: Create `.gitignore`**

Write `.gitignore`:
```
__pycache__/
*.pyc
.pytest_cache/
.venv/
venv/
.DS_Store
```

- [ ] **Step 5: Install dev deps locally and confirm pytest runs**

Run:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r scripts/requirements-dev.txt
pytest --version
```
Expected: `pytest 8.3.3` (or compatible) printed.

- [ ] **Step 6: Commit**

```bash
git add scripts/requirements.txt scripts/requirements-dev.txt scripts/__init__.py scripts/tests/__init__.py scripts/tests/fixtures/.gitkeep .gitignore
git commit -m "Bootstrap dashboard generator project structure"
```

---

### Task 2: Seed `config.yml` with design values

**Files:**
- Create: `config.yml`

- [ ] **Step 1: Write `config.yml` with all keys from the spec, seeded from the design**

```yaml
handle: 8enji
machine: dashboard
website: bencharest.com

me:
  os: "macOS 15.4 · arm64"
  shell: "zsh 5.9"
  editor: "nvim · 0.10.2"
  wm: "aerospace"
  theme: "tokyonight-storm"
  uptime_from: "2016-09-22"

now:
  building: "a tiny static-site engine in rust"
  listening: "tycho — awake (vinyl rip)"
  learning: "zig · webgpu · papermaking"
  reach: "@8enji · ben@bencharest.com"

statusbar:
  cpu: "4%"
  mem: "412mb"
  net: "▲ 1.2mb/s"
  version: "v2.6.0"

ascii_art: |
                  ;:cloolc;,'.
              'cdkOOOkkxxxxdolc;'.
           .;okOOOOOOOOOkkxxxxddol:,.
         .;dkOOOOOOOOOOOOOkkxxxxddool:.
       .,lxOOOOOOOOOOOOOOOOOkkxxxxddooll;.
      .;dOOOOOOOOOOOOOOOOOOOOOkkxxxxdoool:.
     .:xOOOOOOOOOOOOOOOOOOOOOOOOkkxxxdoooo:.
    .;xOOOOOOOOOOOOOOOOOOOOOOOOOkkkxxxdooool.
    ,oOOOOOOOOOO0K0OOOOOO0K0OOOOkkkxxxdoooool
   .lOOOOOOOOOOKWMWXOOOOXMMWKOOOkkkxxxdooooooc
   .lOOOOOOOOOOOXMMNOOOOXMMNOOOOkkkxxxxdooollc
   .cOOOOOOOOOOOOKK0OOOOO0KKOOOOkkkxxxxdoollll
    ;kOOOOOOOOOOOOOOOOOOOOOOOOOkkkxxxxdoollll;
    .lOOOOO0K0OOOOOOOOOOOOOOOO0K0OOkkxxxdoolll
     ,xOOOOXMW0kkOOOOOOOOOOOOXMMNOOOkkxxxdooo:
     .cOOOO0NMWNXKKKKKKKKKXNNWMMKOOOkkkxxxxdo,
      .ckOOOO0XWMMMMMMMMMMMMMWNKOOkkkxxxxxxo:.
       .;xOOOOOO0KXNWWWWWWNXK0OOkkkxxxxxxxd:.
         'lkOOOOOOOOO0000OOOOOOkkkxxxxxxxo,.
           .:dkOOOOOOOOOOOOOOOkkkxxxxxdo;.
             .,cdxkOOOOOOOOOOkkxxxxddl;.
                .';clddxxkkkxxxddlc;'.
                     ..',;:::;,'..
```

- [ ] **Step 2: Verify YAML parses**

Run:
```bash
python3 -c "import yaml; print(yaml.safe_load(open('config.yml'))['handle'])"
```
Expected: `8enji`

- [ ] **Step 3: Commit**

```bash
git add config.yml
git commit -m "Add config.yml seeded from design values"
```

---

### Task 3: Layout constants + helpers + window chrome

**Files:**
- Create: `scripts/render.py`
- Create: `scripts/tests/test_render_chrome.py`

The render module starts with shared constants and primitives. Window chrome = the outer rounded rectangle + titlebar (traffic lights + title text).

- [ ] **Step 1: Write the failing test**

Write `scripts/tests/test_render_chrome.py`:
```python
from scripts.render import render_chrome, CANVAS_W


def test_chrome_contains_traffic_lights():
    svg = render_chrome(title_left="8enji", title_right="dashboard")
    assert 'fill="#ff5f57"' in svg
    assert 'fill="#febc2e"' in svg
    assert 'fill="#28c840"' in svg


def test_chrome_contains_title_text():
    svg = render_chrome(title_left="8enji", title_right="dashboard")
    assert "8enji.dashboard" in svg or ("8enji" in svg and "dashboard" in svg)


def test_canvas_width_is_1500():
    assert CANVAS_W == 1500
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest scripts/tests/test_render_chrome.py -v
```
Expected: `ImportError` (module not found) or `ModuleNotFoundError`.

- [ ] **Step 3: Implement minimal render.py**

Write `scripts/render.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```bash
pytest scripts/tests/test_render_chrome.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/render.py scripts/tests/test_render_chrome.py
git commit -m "Add SVG window chrome rendering"
```

---

### Task 4: Statusbar rendering

**Files:**
- Modify: `scripts/render.py`
- Create: `scripts/tests/test_render_statusbar.py`

- [ ] **Step 1: Write the failing test**

Write `scripts/tests/test_render_statusbar.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest scripts/tests/test_render_statusbar.py -v
```
Expected: `ImportError: cannot import name 'render_statusbar'`.

- [ ] **Step 3: Implement `render_statusbar` in `scripts/render.py`**

Append to `scripts/render.py`:
```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run:
```bash
pytest scripts/tests/ -v
```
Expected: all tests pass (chrome + statusbar = 5 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/render.py scripts/tests/test_render_statusbar.py
git commit -m "Add statusbar rendering"
```

---

### Task 5: Panel primitive (border + heading)

Every panel shares the same outer frame: a rounded `<rect>` border plus a small uppercase header row with left label and right metadata. Build this primitive once.

**Files:**
- Modify: `scripts/render.py`
- Create: `scripts/tests/test_render_panel.py`

- [ ] **Step 1: Write the failing test**

Write `scripts/tests/test_render_panel.py`:
```python
from scripts.render import render_panel_frame


def test_panel_frame_has_border_and_header():
    svg = render_panel_frame(x=14, y=60, w=680, h=400, label="me", right="/etc/8enji.png")
    assert "me" in svg.lower()
    assert "/etc/8enji.png" in svg
    assert 'rx="9"' in svg  # rounded border
```

- [ ] **Step 2: Run test to verify it fails**

Run:
```bash
pytest scripts/tests/test_render_panel.py -v
```
Expected: import error.

- [ ] **Step 3: Implement `render_panel_frame`**

Append to `scripts/render.py`:
```python
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
```

- [ ] **Step 4: Run tests to verify pass**

Run:
```bash
pytest scripts/tests/ -v
```
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/render.py scripts/tests/test_render_panel.py
git commit -m "Add panel frame primitive"
```

---

### Task 6: ME panel (ASCII portrait + sysinfo + footer)

**Files:**
- Modify: `scripts/render.py`
- Create: `scripts/tests/test_render_me.py`

The ME panel has the largest content density: ASCII portrait on the left, sysinfo key/value table on the right, footer with handle + status.

**Layout inside the panel (relative to panel x,y):**
- ASCII portrait starts at (22, 56), font-size 8px, line-height 1.05em — left column ~340px wide
- Sysinfo block aligned vertically center, starts at (380, ~panel-mid), 7 rows of `<key> <value>`
- Footer at the bottom 30px above panel bottom, full panel width

- [ ] **Step 1: Write the failing test**

Write `scripts/tests/test_render_me.py`:
```python
from datetime import date
from scripts.render import render_me_panel


CONFIG = {
    "handle": "8enji",
    "machine": "dashboard",
    "website": "bencharest.com",
    "me": {
        "os": "macOS 15.4 · arm64",
        "shell": "zsh 5.9",
        "editor": "nvim · 0.10.2",
        "wm": "aerospace",
        "theme": "tokyonight-storm",
        "uptime_from": "2016-09-22",
    },
    "ascii_art": "AAAA\nBBBB\nCCCC\n",
}


def test_me_panel_renders_handle_and_machine():
    svg = render_me_panel(CONFIG, x=14, y=60, w=680, h=426, today=date(2026, 5, 14))
    assert "8enji" in svg
    assert "dashboard" in svg


def test_me_panel_renders_all_sysinfo_keys():
    svg = render_me_panel(CONFIG, x=14, y=60, w=680, h=426, today=date(2026, 5, 14))
    for key in ("host", "os", "shell", "editor", "wm", "theme", "uptime"):
        assert key in svg


def test_me_panel_renders_sysinfo_values():
    svg = render_me_panel(CONFIG, x=14, y=60, w=680, h=426, today=date(2026, 5, 14))
    assert "macOS 15.4" in svg
    assert "zsh 5.9" in svg
    assert "tokyonight-storm" in svg


def test_me_panel_renders_uptime():
    svg = render_me_panel(CONFIG, x=14, y=60, w=680, h=426, today=date(2026, 5, 14))
    # 2016-09-22 to 2026-05-14 = 9 years, 234 days
    assert "9y" in svg
    assert "234d" in svg


def test_me_panel_renders_footer_status():
    svg = render_me_panel(CONFIG, x=14, y=60, w=680, h=426, today=date(2026, 5, 14))
    assert "online" in svg.lower()
    assert "bencharest.com" in svg


def test_me_panel_renders_ascii_lines():
    svg = render_me_panel(CONFIG, x=14, y=60, w=680, h=426, today=date(2026, 5, 14))
    assert "AAAA" in svg
    assert "BBBB" in svg
    assert "CCCC" in svg
```

- [ ] **Step 2: Run tests to verify they fail**

Run:
```bash
pytest scripts/tests/test_render_me.py -v
```
Expected: import error.

- [ ] **Step 3: Implement `render_me_panel` and uptime helper in `scripts/render.py`**

Append to `scripts/render.py`:
```python
from datetime import date


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
```

- [ ] **Step 4: Run tests to verify pass**

Run:
```bash
pytest scripts/tests/test_render_me.py -v
```
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/render.py scripts/tests/test_render_me.py
git commit -m "Add ME panel rendering"
```

---

### Task 7: LANGUAGES panel (bars with diagonal hatch trough)

**Files:**
- Modify: `scripts/render.py`
- Create: `scripts/tests/test_render_languages.py`

The panel shows up to 6 rows: name on the left (88px), bar in the middle, percentage on the right (44px). Each bar has a faint diagonal hatch background (trough) + a solid fill rectangle whose width is the percentage.

- [ ] **Step 1: Write the failing test**

Write `scripts/tests/test_render_languages.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify fail**

Run:
```bash
pytest scripts/tests/test_render_languages.py -v
```
Expected: import error.

- [ ] **Step 3: Implement `render_languages_panel`**

Append to `scripts/render.py`:
```python
LANG_COLOR_MAP = {
    "typescript": COLORS["ts"],
    "javascript": COLORS["ts"],
    "python": COLORS["py"],
    "go": COLORS["go"],
    "rust": COLORS["rust"],
    "lua": COLORS["lua"],
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
```

- [ ] **Step 4: Run tests to verify pass**

Run:
```bash
pytest scripts/tests/test_render_languages.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/render.py scripts/tests/test_render_languages.py
git commit -m "Add LANGUAGES panel with hatched bars"
```

---

### Task 8: ACTIVITY panel (60-day bar chart)

**Files:**
- Modify: `scripts/render.py`
- Create: `scripts/tests/test_render_activity.py`

60 vertical bars rising from a baseline, peak normalized to ~100% of chart height. Axis labels (60d/45d/30d/15d/today) below.

- [ ] **Step 1: Write the failing test**

Write `scripts/tests/test_render_activity.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify fail**

Run:
```bash
pytest scripts/tests/test_render_activity.py -v
```
Expected: import error.

- [ ] **Step 3: Implement `render_activity_panel`**

Append to `scripts/render.py`:
```python
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
```

- [ ] **Step 4: Run tests to verify pass**

Run:
```bash
pytest scripts/tests/test_render_activity.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/render.py scripts/tests/test_render_activity.py
git commit -m "Add ACTIVITY panel bar chart rendering"
```

---

### Task 9: STATS panel (rows + top repos)

**Files:**
- Modify: `scripts/render.py`
- Create: `scripts/tests/test_render_stats.py`

5 numeric rows separated by dotted lines, then a "top repos" sub-block with 3 rows.

- [ ] **Step 1: Write the failing test**

Write `scripts/tests/test_render_stats.py`:
```python
from scripts.render import render_stats_panel, format_compact, format_loc


STATS = {
    "repos": 42,
    "stars": 214,
    "followers": 89,
    "commits": 3128,
    "loc_bytes": 12_050_000,  # ~241k lines at 50 bytes/line
    "top_repos": [
        {"name": "static-rs", "language": "rust", "stars": 84},
        {"name": "tinybuf", "language": "go", "stars": 51},
        {"name": "dotfiles", "language": "lua", "stars": 37},
    ],
}


def test_format_compact():
    assert format_compact(3128) == "3,128"
    assert format_compact(214) == "214"


def test_format_loc():
    assert format_loc(12_050_000) == "241k"
    assert format_loc(500_000) == "10k"


def test_stats_renders_all_stat_labels():
    svg = render_stats_panel(STATS, x=708, y=500, w=778, h=354)
    for k in ("repos", "stars", "followers", "commits", "loc"):
        assert k in svg


def test_stats_renders_stat_values():
    svg = render_stats_panel(STATS, x=708, y=500, w=778, h=354)
    assert "42" in svg
    assert "214" in svg
    assert "89" in svg
    assert "3,128" in svg
    assert "241k" in svg


def test_stats_renders_top_repos():
    svg = render_stats_panel(STATS, x=708, y=500, w=778, h=354)
    for r in STATS["top_repos"]:
        assert r["name"] in svg
        assert r["language"] in svg
        assert str(r["stars"]) in svg


def test_stats_renders_live_indicator():
    svg = render_stats_panel(STATS, x=708, y=500, w=778, h=354)
    assert "live" in svg.lower() or "LIVE" in svg
```

- [ ] **Step 2: Run tests to verify fail**

Run:
```bash
pytest scripts/tests/test_render_stats.py -v
```
Expected: import error.

- [ ] **Step 3: Implement helpers and `render_stats_panel`**

Append to `scripts/render.py`:
```python
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
```

- [ ] **Step 4: Run tests to verify pass**

Run:
```bash
pytest scripts/tests/test_render_stats.py -v
```
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/render.py scripts/tests/test_render_stats.py
git commit -m "Add STATS panel rendering"
```

---

### Task 10: NOW panel (2x2 grid)

**Files:**
- Modify: `scripts/render.py`
- Create: `scripts/tests/test_render_now.py`

Spans the full width of the grid; two columns. Per chat transcript: building/listening on left, learning/reach on right.

- [ ] **Step 1: Write the failing test**

Write `scripts/tests/test_render_now.py`:
```python
from scripts.render import render_now_panel


CFG = {
    "now": {
        "building": "a tiny static-site engine in rust",
        "listening": "tycho — awake (vinyl rip)",
        "learning": "zig · webgpu · papermaking",
        "reach": "@8enji · ben@bencharest.com",
    }
}


def test_now_renders_all_four_keys():
    svg = render_now_panel(CFG, x=14, y=870, w=1472, h=120)
    for k in ("building", "listening", "learning", "reach"):
        assert k in svg


def test_now_renders_all_values():
    svg = render_now_panel(CFG, x=14, y=870, w=1472, h=120)
    assert "static-site engine in rust" in svg
    assert "tycho" in svg
    assert "zig" in svg
    assert "@8enji" in svg


def test_now_panel_header():
    svg = render_now_panel(CFG, x=14, y=870, w=1472, h=120)
    assert "/etc/8enji.conf" in svg
```

- [ ] **Step 2: Run tests to verify fail**

Run:
```bash
pytest scripts/tests/test_render_now.py -v
```
Expected: import error.

- [ ] **Step 3: Implement `render_now_panel`**

Append to `scripts/render.py`:
```python
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
```

- [ ] **Step 4: Run tests to verify pass**

Run:
```bash
pytest scripts/tests/test_render_now.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/render.py scripts/tests/test_render_now.py
git commit -m "Add NOW panel rendering"
```

---

### Task 11: Top-level `render()` + golden snapshot

**Files:**
- Modify: `scripts/render.py`
- Create: `scripts/tests/fixtures/sample_data.json`
- Create: `scripts/tests/fixtures/sample_config.yml`
- Create: `scripts/tests/test_render_full.py`
- Create: `scripts/tests/fixtures/expected.svg` (generated, see Step 5)

Compose all panels into the full document.

**Layout (fixed):**
- Canvas: `1500 × 1024`
- Outer padding: 14px
- Titlebar: 45px tall at top
- Statusbar: 36px tall at bottom
- Grid:
  - Column split: col1 width 678, col2 width 780, gap 14, both starting at x=14
  - Row 1 (ME, LANGUAGES): y=59 to y=485, height 426
  - Row 2 (ACTIVITY, STATS): y=499 to y=853, height 354
  - Row 3 (NOW spans both): y=867 to y=973 — width 1472, height 106
- Statusbar at y=988

- [ ] **Step 1: Write the sample fixtures**

Write `scripts/tests/fixtures/sample_data.json`:
```json
{
  "followers": 89,
  "public_repos": 42,
  "total_stars": 214,
  "total_commits": 3128,
  "total_loc_bytes": 12050000,
  "languages": [
    ["typescript", 42.0],
    ["python", 23.0],
    ["go", 14.0],
    ["rust", 11.0],
    ["lua", 6.0],
    ["other", 4.0]
  ],
  "activity": [38, 52, 41, 64, 30, 58, 47, 71, 44, 36, 55, 62, 28, 49, 73, 81, 56, 44, 67, 52, 33, 48, 60, 92, 71, 54, 39, 66, 50, 78, 43, 57, 49, 70, 35, 62, 48, 81, 56, 44, 66, 50, 38, 72, 59, 47, 64, 51, 42, 75, 58, 46, 69, 53, 41, 64, 50, 72, 59, 47],
  "activity_peak": 92,
  "activity_streak": 142,
  "activity_avg": 14.3,
  "top_repos": [
    {"name": "static-rs", "language": "rust", "stars": 84},
    {"name": "tinybuf", "language": "go", "stars": 51},
    {"name": "dotfiles", "language": "lua", "stars": 37}
  ]
}
```

Write `scripts/tests/fixtures/sample_config.yml`: copy `config.yml` from the repo root.

```bash
cp config.yml scripts/tests/fixtures/sample_config.yml
```

- [ ] **Step 2: Write the failing snapshot test**

Write `scripts/tests/test_render_full.py`:
```python
import json
from datetime import datetime, timezone
from pathlib import Path

import yaml

from scripts.render import render


FIXTURES = Path(__file__).parent / "fixtures"


def test_render_full_snapshot():
    config = yaml.safe_load((FIXTURES / "sample_config.yml").read_text())
    data = json.loads((FIXTURES / "sample_data.json").read_text())
    ts = datetime(2026, 5, 14, 14, 23, 8, tzinfo=timezone.utc)

    actual = render(config, data, ts)
    expected_path = FIXTURES / "expected.svg"
    expected = expected_path.read_text() if expected_path.exists() else ""

    if actual != expected:
        # Convenient debug: write actual.svg next to expected.svg
        (FIXTURES / "actual.svg").write_text(actual)
        assert actual == expected, "SVG differs from expected.svg (see actual.svg)"


def test_render_returns_full_svg_document():
    config = yaml.safe_load((FIXTURES / "sample_config.yml").read_text())
    data = json.loads((FIXTURES / "sample_data.json").read_text())
    ts = datetime(2026, 5, 14, 14, 23, 8, tzinfo=timezone.utc)

    svg = render(config, data, ts)
    assert svg.startswith("<?xml") or svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    assert 'viewBox="0 0 1500 1024"' in svg
```

- [ ] **Step 3: Run tests to verify they fail**

Run:
```bash
pytest scripts/tests/test_render_full.py -v
```
Expected: `ImportError: cannot import name 'render'`.

- [ ] **Step 4: Implement top-level `render()`**

Append to `scripts/render.py`:
```python
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
```

- [ ] **Step 5: Run the renderer once to generate the expected snapshot**

Run:
```bash
python3 -c "
import json, yaml
from datetime import datetime, timezone
from scripts.render import render
config = yaml.safe_load(open('scripts/tests/fixtures/sample_config.yml'))
data = json.load(open('scripts/tests/fixtures/sample_data.json'))
ts = datetime(2026, 5, 14, 14, 23, 8, tzinfo=timezone.utc)
open('scripts/tests/fixtures/expected.svg', 'w').write(render(config, data, ts))
"
```

Then re-run the test:
```bash
pytest scripts/tests/test_render_full.py -v
```
Expected: 2 passed.

- [ ] **Step 6: Visual sanity check**

Open `scripts/tests/fixtures/expected.svg` in a browser (drag-and-drop or `open scripts/tests/fixtures/expected.svg` on macOS). Verify:
- All five panels visible
- ME panel shows ASCII portrait + sysinfo
- LANGUAGES bars are present and colored
- ACTIVITY chart shows 60 bars with axis labels
- STATS shows numbers + top repos
- NOW shows 2x2 grid
- Statusbar at bottom
- No overlapping text, no clipped content

If anything looks wrong, fix coordinates in `render.py` and regenerate `expected.svg` (Step 5).

- [ ] **Step 7: Commit**

```bash
git add scripts/render.py scripts/tests/test_render_full.py scripts/tests/fixtures/sample_data.json scripts/tests/fixtures/sample_config.yml scripts/tests/fixtures/expected.svg
git commit -m "Add top-level render() and golden snapshot test"
```

---

### Task 12: GitHub API client — user + repos

**Files:**
- Create: `scripts/github_data.py`
- Create: `scripts/tests/test_github_user_repos.py`

- [ ] **Step 1: Write the failing test**

Write `scripts/tests/test_github_user_repos.py`:
```python
import responses

from scripts.github_data import GitHubClient


@responses.activate
def test_fetch_user():
    responses.get(
        "https://api.github.com/users/8enji",
        json={"login": "8enji", "followers": 89, "public_repos": 42},
        status=200,
    )
    client = GitHubClient(token="t", user="8enji")
    user = client.fetch_user()
    assert user["followers"] == 89
    assert user["public_repos"] == 42


@responses.activate
def test_fetch_repos_excludes_forks():
    responses.get(
        "https://api.github.com/users/8enji/repos",
        json=[
            {"name": "a", "fork": False, "stargazers_count": 10, "language": "Python"},
            {"name": "b", "fork": True, "stargazers_count": 5, "language": "Go"},
            {"name": "c", "fork": False, "stargazers_count": 3, "language": "Rust"},
        ],
        status=200,
    )
    client = GitHubClient(token="t", user="8enji")
    repos = client.fetch_repos()
    assert [r["name"] for r in repos] == ["a", "c"]


@responses.activate
def test_fetch_repos_sends_auth_header():
    responses.get(
        "https://api.github.com/users/8enji/repos",
        json=[],
        status=200,
    )
    client = GitHubClient(token="my-token", user="8enji")
    client.fetch_repos()
    assert responses.calls[0].request.headers["Authorization"] == "Bearer my-token"
```

- [ ] **Step 2: Run tests to verify fail**

Run:
```bash
pytest scripts/tests/test_github_user_repos.py -v
```
Expected: import error.

- [ ] **Step 3: Implement `GitHubClient.fetch_user` and `fetch_repos`**

Write `scripts/github_data.py`:
```python
"""GitHub API fetchers for the dashboard generator."""

import requests


GITHUB_API = "https://api.github.com"
GITHUB_GRAPHQL = "https://api.github.com/graphql"


class GitHubClient:
    def __init__(self, token: str, user: str):
        self.token = token
        self.user = user
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def fetch_user(self) -> dict:
        r = self.session.get(f"{GITHUB_API}/users/{self.user}", timeout=15)
        r.raise_for_status()
        return r.json()

    def fetch_repos(self) -> list[dict]:
        """All non-fork repos owned by the user."""
        repos: list[dict] = []
        page = 1
        while True:
            r = self.session.get(
                f"{GITHUB_API}/users/{self.user}/repos",
                params={"per_page": 100, "page": page, "sort": "updated", "type": "owner"},
                timeout=15,
            )
            r.raise_for_status()
            chunk = r.json()
            if not chunk:
                break
            repos.extend(chunk)
            if len(chunk) < 100:
                break
            page += 1
        return [r for r in repos if not r.get("fork")]
```

- [ ] **Step 4: Run tests to verify pass**

Run:
```bash
pytest scripts/tests/test_github_user_repos.py -v
```
Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add scripts/github_data.py scripts/tests/test_github_user_repos.py
git commit -m "Add GitHub client: fetch_user and fetch_repos"
```

---

### Task 13: GitHub API client — languages + aggregation

**Files:**
- Modify: `scripts/github_data.py`
- Create: `scripts/tests/test_github_languages.py`

- [ ] **Step 1: Write the failing test**

Write `scripts/tests/test_github_languages.py`:
```python
import responses

from scripts.github_data import GitHubClient, aggregate_languages


@responses.activate
def test_fetch_repo_languages():
    responses.get(
        "https://api.github.com/repos/8enji/foo/languages",
        json={"TypeScript": 1000, "Python": 500},
        status=200,
    )
    client = GitHubClient(token="t", user="8enji")
    langs = client.fetch_repo_languages("8enji", "foo")
    assert langs == {"TypeScript": 1000, "Python": 500}


def test_aggregate_languages_sums_top_five_plus_other():
    repo_langs = {
        "a": {"TypeScript": 4200, "Python": 1000},
        "b": {"Python": 1300, "Go": 1400, "Rust": 1100},
        "c": {"Lua": 600, "Shell": 200, "Vim Script": 200},
    }
    result = aggregate_languages(repo_langs)
    names = [n for n, _ in result]
    assert names[0] == "typescript"
    assert "other" in names
    # Sum should be ~100%
    total_pct = sum(p for _, p in result)
    assert 99.0 <= total_pct <= 101.0


def test_aggregate_languages_returns_at_most_six_rows():
    repo_langs = {"r": {f"L{i}": 1000 for i in range(20)}}
    result = aggregate_languages(repo_langs)
    assert len(result) <= 6
```

- [ ] **Step 2: Run tests to verify fail**

Run:
```bash
pytest scripts/tests/test_github_languages.py -v
```
Expected: import error for `aggregate_languages` (and `fetch_repo_languages`).

- [ ] **Step 3: Add `fetch_repo_languages` as a method on `GitHubClient`**

Inside the `GitHubClient` class in `scripts/github_data.py`, after the `fetch_repos` method, add:
```python
    def fetch_repo_languages(self, owner: str, repo: str) -> dict[str, int]:
        r = self.session.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/languages", timeout=15
        )
        r.raise_for_status()
        return r.json()
```

- [ ] **Step 4: Add `aggregate_languages` at module level**

Append to the end of `scripts/github_data.py`:
```python
def aggregate_languages(
    repo_langs: dict[str, dict[str, int]],
) -> list[tuple[str, float]]:
    """Combine per-repo language bytes into top-5 lowercased + 'other' percentages."""
    totals: dict[str, int] = {}
    for langs in repo_langs.values():
        for name, n in langs.items():
            totals[name] = totals.get(name, 0) + n

    grand = sum(totals.values()) or 1
    sorted_langs = sorted(totals.items(), key=lambda kv: -kv[1])
    top = sorted_langs[:5]
    rest_bytes = sum(n for _, n in sorted_langs[5:])
    out = [(name.lower(), n * 100 / grand) for name, n in top]
    if rest_bytes:
        out.append(("other", rest_bytes * 100 / grand))
    return out
```

- [ ] **Step 5: Run tests to verify pass**

Run:
```bash
pytest scripts/tests/test_github_languages.py -v
```
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add scripts/github_data.py scripts/tests/test_github_languages.py
git commit -m "Add language fetching and aggregation"
```

---

### Task 14: GitHub API client — contributions (GraphQL) + activity helpers

**Files:**
- Modify: `scripts/github_data.py`
- Create: `scripts/tests/test_github_contributions.py`

GraphQL endpoint returns a contribution calendar: weeks → contributionDays with date + contributionCount. We slice the last 60 days.

- [ ] **Step 1: Write the failing test**

Write `scripts/tests/test_github_contributions.py`:
```python
import json
from datetime import date

import responses

from scripts.github_data import GitHubClient, extract_activity


GRAPHQL_PAYLOAD = {
    "data": {
        "user": {
            "contributionsCollection": {
                "totalCommitContributions": 3128,
                "contributionCalendar": {
                    "weeks": [
                        {
                            "contributionDays": [
                                {"date": "2026-05-12", "contributionCount": 5},
                                {"date": "2026-05-13", "contributionCount": 8},
                                {"date": "2026-05-14", "contributionCount": 12},
                            ]
                        }
                    ]
                },
            }
        }
    }
}


@responses.activate
def test_fetch_contributions():
    responses.post("https://api.github.com/graphql", json=GRAPHQL_PAYLOAD, status=200)
    client = GitHubClient(token="t", user="8enji")
    result = client.fetch_contributions(today=date(2026, 5, 14))
    assert result["total_commits"] == 3128
    assert result["days"][("2026-05-14")] == 12


def test_extract_activity_last_60_days_pads_zeros():
    days = {"2026-05-13": 8, "2026-05-14": 12}
    activity = extract_activity(days, today=date(2026, 5, 14), window=60)
    assert len(activity) == 60
    assert activity[-1] == 12   # today
    assert activity[-2] == 8    # yesterday
    assert activity[0] == 0     # 59 days before today, no data


def test_extract_activity_computes_avg_and_peak():
    days = {"2026-05-13": 8, "2026-05-14": 12}
    activity = extract_activity(days, today=date(2026, 5, 14), window=60)
    from statistics import mean
    avg = mean(activity)
    peak = max(activity)
    assert peak == 12
    assert 0.3 < avg < 0.4
```

- [ ] **Step 2: Run tests to verify fail**

Run:
```bash
pytest scripts/tests/test_github_contributions.py -v
```
Expected: import error.

- [ ] **Step 3: Implement `fetch_contributions` and `extract_activity`**

Add inside `GitHubClient` class:
```python
    def fetch_contributions(self, today: date) -> dict:
        from datetime import datetime, time, timedelta, timezone

        end = datetime.combine(today, time(23, 59, 59), tzinfo=timezone.utc)
        start = end - timedelta(days=365)
        query = """
        query($login: String!, $from: DateTime!, $to: DateTime!) {
          user(login: $login) {
            contributionsCollection(from: $from, to: $to) {
              totalCommitContributions
              contributionCalendar {
                weeks {
                  contributionDays {
                    date
                    contributionCount
                  }
                }
              }
            }
          }
        }
        """
        r = self.session.post(
            GITHUB_GRAPHQL,
            json={
                "query": query,
                "variables": {
                    "login": self.user,
                    "from": start.isoformat(),
                    "to": end.isoformat(),
                },
            },
            timeout=20,
        )
        r.raise_for_status()
        payload = r.json()
        cc = payload["data"]["user"]["contributionsCollection"]
        days: dict[str, int] = {}
        for week in cc["contributionCalendar"]["weeks"]:
            for d in week["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
        return {"total_commits": cc["totalCommitContributions"], "days": days}
```

Append at module level (also requires `from datetime import date, timedelta` at the top of the file):
```python
from datetime import date, timedelta


def extract_activity(days: dict[str, int], today: date, window: int = 60) -> list[int]:
    """Return `window` daily counts ending at `today` (oldest first, today last)."""
    out: list[int] = []
    for i in range(window - 1, -1, -1):
        d = today - timedelta(days=i)
        out.append(days.get(d.isoformat(), 0))
    return out
```

- [ ] **Step 4: Run tests to verify pass**

Run:
```bash
pytest scripts/tests/ -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/github_data.py scripts/tests/test_github_contributions.py
git commit -m "Add contributions GraphQL fetch and 60-day activity extraction"
```

---

### Task 15: `fetch_all` — compose `DashboardData`

**Files:**
- Modify: `scripts/github_data.py`
- Create: `scripts/tests/test_github_fetch_all.py`

This is the public composition: one call, one nested dict matching what `render()` consumes.

- [ ] **Step 1: Write the failing test**

Write `scripts/tests/test_github_fetch_all.py`:
```python
from datetime import date

import responses

from scripts.github_data import GitHubClient


@responses.activate
def test_fetch_all_composes_dashboard_data():
    responses.get(
        "https://api.github.com/users/8enji",
        json={"login": "8enji", "followers": 89, "public_repos": 42},
        status=200,
    )
    responses.get(
        "https://api.github.com/users/8enji/repos",
        json=[
            {"name": "static-rs", "owner": {"login": "8enji"}, "fork": False,
             "stargazers_count": 84, "language": "Rust"},
            {"name": "tinybuf", "owner": {"login": "8enji"}, "fork": False,
             "stargazers_count": 51, "language": "Go"},
            {"name": "dotfiles", "owner": {"login": "8enji"}, "fork": False,
             "stargazers_count": 37, "language": "Lua"},
        ],
        status=200,
    )
    responses.get(
        "https://api.github.com/repos/8enji/static-rs/languages",
        json={"Rust": 80000},
        status=200,
    )
    responses.get(
        "https://api.github.com/repos/8enji/tinybuf/languages",
        json={"Go": 40000},
        status=200,
    )
    responses.get(
        "https://api.github.com/repos/8enji/dotfiles/languages",
        json={"Lua": 20000},
        status=200,
    )
    responses.post(
        "https://api.github.com/graphql",
        json={"data": {"user": {"contributionsCollection": {
            "totalCommitContributions": 3128,
            "contributionCalendar": {"weeks": [{"contributionDays": [
                {"date": "2026-05-14", "contributionCount": 12}
            ]}]},
        }}}},
        status=200,
    )

    client = GitHubClient(token="t", user="8enji")
    data = client.fetch_all(today=date(2026, 5, 14))

    assert data["followers"] == 89
    assert data["public_repos"] == 42
    assert data["total_stars"] == 84 + 51 + 37
    assert data["total_commits"] == 3128
    assert data["total_loc_bytes"] == 140000
    assert len(data["activity"]) == 60
    assert data["activity"][-1] == 12
    assert data["top_repos"][0]["name"] == "static-rs"
    assert isinstance(data["activity_avg"], float)
    assert data["activity_peak"] >= 12
```

- [ ] **Step 2: Run test to verify fail**

Run:
```bash
pytest scripts/tests/test_github_fetch_all.py -v
```
Expected: `AttributeError: 'GitHubClient' object has no attribute 'fetch_all'`.

- [ ] **Step 3: Implement `fetch_all`**

Add to `GitHubClient`:
```python
    def fetch_all(self, today: date) -> dict:
        user = self.fetch_user()
        repos = self.fetch_repos()
        repo_langs: dict[str, dict[str, int]] = {}
        for r in repos:
            owner = r["owner"]["login"]
            name = r["name"]
            repo_langs[name] = self.fetch_repo_languages(owner, name)

        languages = aggregate_languages(repo_langs)
        total_loc_bytes = sum(
            n for langs in repo_langs.values() for n in langs.values()
        )

        contrib = self.fetch_contributions(today=today)
        activity = extract_activity(contrib["days"], today=today, window=60)
        activity_avg = sum(activity) / len(activity) if activity else 0.0
        activity_peak = max(activity) if activity else 0
        streak = 0
        for v in reversed(activity):
            if v > 0:
                streak += 1
            else:
                break

        top_repos = sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:3]
        top_repos_clean = [
            {
                "name": r["name"],
                "language": (r.get("language") or "").lower(),
                "stars": r.get("stargazers_count", 0),
            }
            for r in top_repos
        ]

        return {
            "followers": user["followers"],
            "public_repos": user["public_repos"],
            "total_stars": sum(r.get("stargazers_count", 0) for r in repos),
            "total_commits": contrib["total_commits"],
            "total_loc_bytes": total_loc_bytes,
            "languages": languages,
            "activity": activity,
            "activity_avg": float(activity_avg),
            "activity_peak": int(activity_peak),
            "activity_streak": streak,
            "top_repos": top_repos_clean,
        }
```

- [ ] **Step 4: Run tests to verify pass**

Run:
```bash
pytest scripts/tests/ -v
```
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add scripts/github_data.py scripts/tests/test_github_fetch_all.py
git commit -m "Add fetch_all to compose full DashboardData"
```

---

### Task 16: `generate.py` entry point

**Files:**
- Create: `scripts/generate.py`

- [ ] **Step 1: Write `generate.py`**

Write `scripts/generate.py`:
```python
"""Entry point: load config, fetch GitHub data, render SVG, write to disk."""

import argparse
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import yaml

from scripts.github_data import GitHubClient
from scripts.render import render


REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config.yml"
OUTPUT_PATH = REPO_ROOT / "dashboard.svg"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="Print SVG to stdout instead of writing to disk")
    parser.add_argument("--from-fixture", action="store_true",
                        help="Use sample fixture data instead of hitting the GitHub API")
    args = parser.parse_args()

    config = yaml.safe_load(CONFIG_PATH.read_text())

    if args.from_fixture:
        fixtures = Path(__file__).parent / "tests" / "fixtures"
        data = json.loads((fixtures / "sample_data.json").read_text())
    else:
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            print("error: GITHUB_TOKEN env var required", file=sys.stderr)
            return 2
        client = GitHubClient(token=token, user=config["handle"])
        data = client.fetch_all(today=date.today())

    timestamp = datetime.now(timezone.utc)
    svg = render(config, data, timestamp)

    if args.dry_run:
        sys.stdout.write(svg)
    else:
        OUTPUT_PATH.write_text(svg)
        print(f"wrote {OUTPUT_PATH} ({len(svg)} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Test the dry-run path locally with fixtures**

Run:
```bash
python3 -m scripts.generate --dry-run --from-fixture > /tmp/dashboard-fixture.svg
head -c 200 /tmp/dashboard-fixture.svg
```
Expected: starts with `<?xml version="1.0" encoding="UTF-8"?>` and contains the dashboard markup.

- [ ] **Step 3: Generate the real dashboard.svg from fixtures (so the repo has one before any API call)**

Run:
```bash
python3 -m scripts.generate --from-fixture
```
Expected: prints `wrote .../dashboard.svg (NNN bytes)`. File `dashboard.svg` appears at repo root.

- [ ] **Step 4: Visual sanity check**

Open `dashboard.svg` in a browser. Confirm it matches the design.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate.py dashboard.svg
git commit -m "Add generate.py entry point and initial dashboard.svg"
```

---

### Task 17: GitHub Actions workflow

**Files:**
- Create: `.github/workflows/update-dashboard.yml`

- [ ] **Step 1: Write the workflow**

Write `.github/workflows/update-dashboard.yml`:
```yaml
name: Update Dashboard

on:
  schedule:
    - cron: '0 */6 * * *'
  push:
    branches: [main]
    paths:
      - 'config.yml'
      - 'scripts/**'
      - '.github/workflows/update-dashboard.yml'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  refresh:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: pip
          cache-dependency-path: scripts/requirements.txt

      - name: Install dependencies
        run: pip install -r scripts/requirements.txt

      - name: Generate dashboard
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python -m scripts.generate

      - name: Commit if changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          if git diff --quiet dashboard.svg; then
            echo "No changes to dashboard.svg"
          else
            git add dashboard.svg
            git commit -m "chore: refresh dashboard"
            git push
          fi
```

- [ ] **Step 2: Lint the YAML**

Run:
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/update-dashboard.yml'))"
```
Expected: no output (valid YAML).

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/update-dashboard.yml
git commit -m "Add GitHub Actions workflow to refresh dashboard"
```

---

### Task 18: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace README contents**

Write `README.md`:
```markdown
![8enji dashboard](./dashboard.svg)
```

- [ ] **Step 2: Verify rendering locally**

Open `README.md` in any markdown previewer (VS Code, GitHub web after push, etc.). Confirm the SVG embeds correctly.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "Replace profile README with embedded dashboard SVG"
```

---

### Task 19: End-to-end live run + verification

**Files:** none (verification only)

- [ ] **Step 1: Run the generator against the live GitHub API locally**

Set up a GitHub personal access token with `public_repo` and `read:user` scope (classic) or fine-grained equivalent. Then:
```bash
GITHUB_TOKEN=ghp_yourTokenHere python3 -m scripts.generate
```
Expected: `wrote .../dashboard.svg (NNN bytes)`, no errors.

- [ ] **Step 2: Inspect the result**

Open `dashboard.svg`. Confirm the numbers reflect your actual GitHub profile (real follower count, real repo list, real activity for the last 60 days). Spot-check at least: follower count matches your profile, top repo names are accurate, activity bars look correct.

- [ ] **Step 3: Run the full test suite once more**

Run:
```bash
pytest scripts/tests/ -v
```
Expected: all tests pass.

- [ ] **Step 4: Push the branch and verify the Action**

After the user pushes the branch to GitHub:
```bash
gh run list --workflow=update-dashboard.yml --limit 3
```
Expected: at least one run (triggered by the push) is in `queued`, `in_progress`, or `completed` state. Use `gh run watch` to follow it.

- [ ] **Step 5: After the action completes, confirm bot commit**

```bash
git pull
git log --oneline -5
```
Expected: a recent `chore: refresh dashboard` commit authored by `github-actions[bot]` (OR no new commit because the regenerated SVG was byte-identical to the committed one — also acceptable).

---

## Self-review notes for the implementer

**File watch list during render work:** SVG coordinate bugs are easy. After every panel task, drop the generated `expected.svg` into a browser and eyeball it. The unit tests only check that strings appear — they won't catch overlapping elements.

**Font fallback:** GitHub will strip the `@font-face` for JetBrains Mono. The rendered SVG on github.com will use `ui-monospace` / `SFMono-Regular` / `Menlo`. That's fine — the design's fallback chain handles it.

**Idempotency check:** if `python -m scripts.generate` produces a byte-identical file twice in a row (with fixture data), the action's `git diff --quiet` gate will correctly skip empty commits. Verify by running it twice locally and checking `git status` shows no diff.

**LOC byte-per-line constant:** `format_loc` divides by 50. If the result is wildly off from a manual count, tune the constant — it doesn't need to be exact, just plausible.
