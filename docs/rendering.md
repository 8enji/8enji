# How the README is rendered

The README itself is one line:

```markdown
![8enji dashboard](./dashboard.svg)
```

Everything visible on the profile page comes from [`dashboard.svg`](../dashboard.svg) — a committed SVG that's regenerated on a schedule. There is no client-side rendering, no external image service, and no Markdown templating. GitHub just serves the static SVG.

## Pipeline at a glance

```
config.yml ──┐
             ├──► scripts/generate.py ──► scripts/render.py ──► dashboard.svg
GitHub API ──┘
```

1. **[`config.yml`](../config.yml)** — static content (handle, ASCII portrait, `me`/`now` blocks, visual `tweaks`).
2. **[`scripts/github_data.py`](../scripts/github_data.py)** — fetches live stats (repos, commits, stars, followers, language byte counts, activity streak) via the GitHub REST + GraphQL APIs.
3. **[`scripts/generate.py`](../scripts/generate.py)** — entry point. Loads the config, calls the GitHub client (or a fixture with `--from-fixture`), then hands both to the renderer and writes the result to `dashboard.svg`.
4. **[`scripts/render.py`](../scripts/render.py)** — pure functions that produce the SVG string. No I/O. Mirrors the neofetch-style design: ASCII portrait on the left, KV info column on the right.

## Renderer layout

`render()` in [scripts/render.py:182](../scripts/render.py:182) builds the SVG top-down:

- **Chrome** — rounded window frame, 40px titlebar with macOS traffic lights and a centered `8enji — -zsh — 96×32` label.
- **ASCII portrait** — one of two source blocks in `config.yml` (`ascii_art_small` or `ascii_art`) chosen by `tweaks.ascii_variant`. Rendered as one `<text>` element with per-line `<tspan>`s.
- **Info column** — stacked sections:
  - prompt line `8enji@dashboard`
  - KV grid (6 rows): `os`, `host`, `shell`, `editor`, `theme`, `uptime` (uptime is computed from `me.uptime_from`)
  - `stats` — 2-column grid filled in row-major order: repos / stars · followers / commits · streak / loc (toggleable)
  - `languages · last 12mo` — top 3 + "other", colored by `LANG_DOT_COLORS` ([scripts/render.py:45](../scripts/render.py:45))
  - `now` — building / learning / listening / reach
  - optional `palette` and `statusbar`

The canvas width is fixed at `CANVAS_W = 1280`. Height is computed after laying out the info column so the content always fits. When the info column is taller than the ASCII (typical for the small variant) the ASCII is vertically centered against it; when the ASCII is taller (typical for the large variant) the info column's inter-section gaps are stretched. The math lives in `_estimate_info_height` ([scripts/render.py:157](../scripts/render.py:157)) and the offset/stretch block in `render`.

Value strings that contain ` · ` (e.g. `macOS 15.4 · arm64`) emit the middle dot as a dim `<tspan>` — see `_render_value_with_dim_dots`.

## Visual knobs

`Tweaks` ([scripts/render.py:85](../scripts/render.py:85)) is loaded from `config.yml`'s `tweaks` block. Defaults mirror the saved `EDITMODE-BEGIN` state of `readme-minimal.html`:

| knob | default | notes |
| --- | --- | --- |
| `ascii_variant` | `small` | switches between `ascii_art_small` and `ascii_art` in config |
| `ascii_size_small` / `ascii_size_large` | 12 / 7 | font-size of the ASCII portrait, per variant |
| `ascii_color` | `#8b95a3` | |
| `accent` | `#b6e04f` | recolors the prompt `@`, the `go` lang dot, the palette swatch, and the statusbar dot |
| `font_size` | 19 | base size for the info column |
| `pad_x` / `pad_y` | 88 / 44 | inner padding (CSS `padding: padY padX (padY+4)`) |
| `gap` | 44 | space between ASCII and info column |
| `show_stats` / `show_languages` / `show_now` | true | optional sections |
| `show_palette` / `show_statusbar` / `show_rule` | false | optional sections |

Unknown keys are silently dropped via `Tweaks.from_config`.

## When it regenerates

[`.github/workflows/update-dashboard.yml`](../.github/workflows/update-dashboard.yml) runs the pipeline:

- every 6 hours (`cron: '0 */6 * * *'`)
- on push to `main` that touches `config.yml`, `scripts/**`, or the workflow file
- manually via `workflow_dispatch`

The job runs `python -m scripts.generate`, then commits `dashboard.svg` if it changed (as `github-actions[bot]`). Recent commits with the message `chore: refresh dashboard` come from this loop.

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

For iterating on the design, [`scripts/preview_server.py`](../scripts/preview_server.py) serves a live HTML preview at [`scripts/preview.html`](../scripts/preview.html) so you can tweak knobs without re-running the pipeline each time.
