# GitHub README Dashboard — Design Spec

**Date:** 2026-05-14
**Repo:** `8enji/8enji` (GitHub profile README repo)
**Status:** Approved, pending implementation plan

## Goal

Replace the current text-based GitHub profile README with a live, auto-updating btop-style terminal dashboard rendered as an SVG image. The dashboard pulls activity, language, and repo stats from the GitHub API every 6 hours and on demand, so the profile always reflects current activity without manual edits.

## Design source

The visual design is from a Claude Design handoff bundle and replicates a btop terminal window with five panels (ME, LANGUAGES, ACTIVITY, STATS, NOW) plus a status bar. Color palette, typography, panel structure, and layout are taken directly from `readme/project/readme.html` in the handoff bundle.

## Architecture

### Repository layout

```
8enji/
├── README.md                       # one-line image embed
├── dashboard.svg                   # generated artifact (committed by bot)
├── config.yml                      # personal/static config (manually edited)
├── scripts/
│   ├── generate.py                 # entry point
│   ├── github_data.py              # GitHub API fetchers
│   ├── render.py                   # pure render(config, data) -> svg_string
│   ├── requirements.txt
│   └── tests/
│       ├── fixtures/
│       │   ├── sample_data.json
│       │   └── expected.svg
│       └── test_render.py
├── .github/workflows/
│   └── update-dashboard.yml        # cron + push + manual trigger
├── BenCharest-Resume.pdf           # untouched
└── transcript.pdf                  # untouched
```

### Component responsibilities

- **`config.yml`** — single source of truth for everything the GitHub API cannot provide. Edited by the user, never written by the bot.
- **`github_data.py`** — every GitHub API call lives here. Returns a single `DashboardData` dict. Pure I/O.
- **`render.py`** — pure function `render(config, data, timestamp) -> str`. No I/O. Easy to unit-test.
- **`generate.py`** — thin glue: load config, fetch data, render SVG, write file atomically.
- **`update-dashboard.yml`** — schedules and runs the generator, commits the result when it changes.

## Data sources

### Static (from `config.yml`)

```yaml
handle: 8enji
machine: dashboard          # the part after @ in the `host` sysinfo row
website: bencharest.com

me:
  os: "macOS 15.4 · arm64"
  shell: "zsh 5.9"
  editor: "nvim · 0.10.2"
  wm: "aerospace"
  theme: "tokyonight-storm"
  uptime_from: "2016-09-22"   # GitHub join date

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
  (multi-line ASCII portrait — same content as the design)
```

### Live (from GitHub API)

| Field | Endpoint / source |
|---|---|
| `followers`, `public_repos` | `GET /users/{user}` |
| Repo list + per-repo stars/language | `GET /users/{user}/repos?per_page=100&sort=updated` |
| Per-repo language bytes | `GET /repos/{owner}/{repo}/languages` |
| Daily commit counts (60d), total commits | GraphQL `viewer.contributionsCollection.contributionCalendar` |
| Total stars | summed from repo list |
| Total LOC (approximate) | sum of all language bytes ÷ 50 |

Forks are excluded from language aggregation and top-repo lists.

### Rate limits

With `GITHUB_TOKEN` the budget is 5000 req/hour. A run costs roughly `1 + 1 + N + 1` calls where `N` is the repo count (one `/languages` per repo). At ~42 repos that's ~45 calls per run, four runs per day → ~180 calls/day. No headroom concern.

## Render strategy

### Canvas

Fixed `1500 × ~720` SVG. GitHub's `<img>` tag handles responsive scaling on small screens.

### Translation: HTML/CSS → SVG

- `:root` CSS variables transplanted verbatim into an inline `<style>` block.
- Each panel is a `<g class="panel">` with absolute coordinates from a layout dict at the top of `render.py`.
- Text uses SVG `<text>` with positioned `<tspan>` lines (no auto-wrap).
- ASCII art rendered as one `<text xml:space="preserve">` with one `<tspan x="…" dy="1.05em">` per line.
- Language and activity bars use `<rect>`. Diagonal hatch trough is an SVG `<pattern>` element.
- Dashed dividers from the design are `<line stroke-dasharray="…">`.
- No outer `box-shadow` (skipped — `<filter>` machinery not worth the complexity).

### Font

Stack matches the design: `"JetBrains Mono", ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`. GitHub strips external font URLs in SVGs, so JetBrains Mono won't load — fallback is the system monospace. The result still reads as a terminal on every platform.

### Time-sensitive fields

- Statusbar `clock` shows the SVG's generation timestamp (UTC), not a live clock.
- ME panel `uptime` is `today - config.me.uptime_from`, formatted as `{years}y {days}d`.
- The "live" dot in the STATS panel header is now meaningful: it confirms the SVG is fresh from the last cron tick.

## Workflow & automation

### Triggers

```yaml
on:
  schedule:
    - cron: '0 */6 * * *'     # 00:00, 06:00, 12:00, 18:00 UTC
  push:
    branches: [main]
    paths:
      - 'config.yml'
      - 'scripts/**'
      - '.github/workflows/update-dashboard.yml'
  workflow_dispatch:
```

### Steps

1. `actions/checkout@v4`
2. `actions/setup-python@v5` with Python 3.12
3. `pip install -r scripts/requirements.txt`
4. `python scripts/generate.py` (with `GITHUB_TOKEN` env)
5. Commit + push `dashboard.svg` **only if `git diff --quiet dashboard.svg` reports a diff**

### Permissions

`contents: write` (needed for the bot to push the regenerated SVG).

### Author identity

Bot commits use:
- `user.name`: `github-actions[bot]`
- `user.email`: `41898282+github-actions[bot]@users.noreply.github.com`

## Error handling

| Failure | Behavior |
|---|---|
| GitHub API error / network failure | Script exits non-zero, action marked failed, `dashboard.svg` unchanged — README never breaks |
| Malformed `config.yml` | YAML parse error surfaced in log, script exits non-zero |
| No change in rendered SVG | `git diff --quiet` skips the commit, action exits success |
| Rate limit hit | Effectively impossible at current volume; would surface as a 403 from the API client |

## Testing

- **Unit (golden file):** `tests/test_render.py` calls `render(config, sample_data, fixed_timestamp)` against `tests/fixtures/sample_data.json` and compares to `tests/fixtures/expected.svg`. Any diff fails the test. The expected file is generated once during implementation by running the renderer against the fixture and committing the output; regenerate deliberately when the design changes.
- **Local manual:** `python scripts/generate.py --dry-run` writes the SVG to stdout for visual inspection without touching the working copy.
- **CI for tests:** not added in v1 to keep the workflow lean. Easy to bolt on later.

## README.md content

Single line:

```markdown
![8enji dashboard](./dashboard.svg)
```

The resume PDF link can be added later if desired; it's not in the v1 scope.

## Non-goals (explicitly excluded)

- Real-time updates between cron ticks
- A serverless rendering endpoint
- Using third-party badge services (github-readme-stats, etc.)
- JavaScript animation in the SVG
- Embedded JetBrains Mono font file
- Outer box-shadow on the window
- Pulling "listening" from Spotify/Last.fm (config-driven instead)
- A test job in CI

## Open questions

None at design time. Implementation may surface minor decisions (e.g., exact byte-per-line constant for the LOC estimate) that will be made by the implementer.
