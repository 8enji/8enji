# How the dashboard SVG is rendered

The dashboard image lives at [`dashboard.svg`](../dashboard.svg) — a committed SVG that's regenerated on a schedule and embedded wherever a profile image is needed (currently in [`README.md`](../README.md) via an attachment).

## Pipeline at a glance

```
config.yml ──┐
             ├──► scripts/generate.py ──► scripts/render.py ──► dashboard.svg
GitHub API ──┘
```

1. **[`config.yml`](../config.yml)** — static content: window `title`, `me` block (handle, host short/long, os, shell, editor, theme, uptime_from, github_url), `now` block, visual `tweaks`, and the `ascii_art` portrait.
2. **[`scripts/github_data.py`](../scripts/github_data.py)** — fetches raw stats (repos, commits, stars, followers, language bytes, contribution streak) via the GitHub REST + GraphQL APIs.
3. **[`scripts/generate.py`](../scripts/generate.py)** — entry point. Loads the config, calls the GitHub client (or a fixture with `--from-fixture`), translates the result into the renderer's data shape, computes `uptime` from `me.uptime_from`, then writes the SVG.
4. **[`scripts/render.py`](../scripts/render.py)** — pure function `render(config, data) -> str`. No I/O.

## Renderer layout

`render()` ([scripts/render.py](../scripts/render.py)) builds the SVG top-down:

- **Chrome** — 50px titlebar with macOS traffic lights at x=22/42/62, centered title from `config["title"]`. The whole window is rounded via a `<clipPath rx="14">` plus a subtle 1px outer border stroke.
- **ASCII portrait** — `config["ascii_art"]` is dedented (common leading indent stripped) and rendered as one `<text>` element with `<tspan dy>` line steps. Sized by `tweaks.ascii_size`.
- **Info column** — stacked sections:
  - prompt: `{me.handle}@{me.host_short}` with a dim `@`
  - KV grid (purple keys): `os`, `host`, `shell`, `editor`, `theme`, `uptime` (uptime is supplied in `data`)
  - `STATS` (toggleable) — 2-column row-major grid: repos / stars · followers / commits · streak / loc, with dotted underlines
  - `LANGUAGES` (toggleable) — top 3 languages by share + an aggregated `other`, each with a colored square dot
  - `NOW` (toggleable) — building / learning / listening / reach
  - `PALETTE` (optional, off by default) — 8 swatches
  - status bar (optional, off by default) — `ONLINE · V2.6.0` plus `me.github_url`

Canvas width is fixed at `CANVAS_W = 1280`. Height is computed from `max(ascii_h, info_h) + 2·pad_y + title_h`. The shorter of the two columns is vertically centered against the taller one.

Value strings get light styling: ` · ` separators dim to muted, and `(parentheticals)` dim as well (see `_colorize_value`).

## Data shape

`render()` expects `data` shaped like:

```python
{
  "repos": 42, "stars": 214, "followers": 89,
  "commits": 3128, "streak": 142,
  "loc": 241000,                 # approximate lines of code; _humanize_loc adds k/m suffix
  "uptime": "9y 142d",            # pre-formatted string
  "languages": {"typescript": 42, "python": 23, ...},  # name → count (or percentage)
}
```

`generate.py` builds this from the github_data fetcher's wider output (renaming `public_repos → repos`, `total_stars → stars`, etc., dividing `total_loc_bytes` by ~50 to get LOC, and turning the language tuple list into a dict).

## Visual knobs

`Tweaks` ([scripts/render.py:55](../scripts/render.py:55)) is loaded from `config.yml`'s `tweaks` block. Defaults:

| knob | default | notes |
| --- | --- | --- |
| `ascii_size` | 12 | font-size of the ASCII portrait |
| `ascii_color` | `#8b95a3` | |
| `accent` | `#b6e04f` | recolors the `go` lang dot, the palette swatch, and the statusbar dot |
| `font_size` | 19 | base size for the info column |
| `pad_x` / `pad_y` | 88 / 44 | inner padding inside the window chrome |
| `gap` | 44 | space between ASCII and info column |
| `show_stats` / `show_languages` / `show_now` | true | optional sections |
| `show_palette` / `show_statusbar` / `show_rule` | false | optional sections |

Unknown keys are silently dropped via `Tweaks.from_config`.

## When it regenerates

[`.github/workflows/update-dashboard.yml`](../.github/workflows/update-dashboard.yml) runs the pipeline every 6 hours, on push to `main` that touches `config.yml`/`scripts/**`/the workflow file, or manually via `workflow_dispatch`. The job commits `dashboard.svg` if it changed (as `github-actions[bot]`).

## Running it locally

```bash
pip install -r scripts/requirements.txt

# Real data — needs a GitHub token in the env
GITHUB_TOKEN=ghp_xxx python -m scripts.generate

# Or use the bundled fixture — no network, no token
python -m scripts.generate --from-fixture

# Print to stdout instead of writing the file
python -m scripts.generate --from-fixture --dry-run
```

For interactive design tweaks, [`scripts/preview_server.py`](../scripts/preview_server.py) serves a live HTML preview at [`scripts/preview.html`](../scripts/preview.html) so you can drag sliders without re-running the pipeline.
