"""GitHub API fetchers for the dashboard generator."""

import requests
from datetime import date, timedelta


GITHUB_API = "https://api.github.com"
GITHUB_GRAPHQL = "https://api.github.com/graphql"


class GitHubClient:
    def __init__(self, token: str, user: str, include_orgs: list[str] | None = None):
        self.token = token
        self.user = user
        # Orgs whose repos are treated as the user's own (e.g. a solo org).
        # Empty → owner-only, the historical behavior.
        self.include_orgs = include_orgs or []
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
        """Non-fork repos owned by the authenticated user, including private
        ones. Uses /user/repos (auth-scoped) so the LOC and repo counts include
        private repos; this assumes the token belongs to `self.user`, which is
        the case for the dashboard's CI workflow.

        When `self.include_orgs` is set, the affiliation is broadened to also
        return repos from orgs the user belongs to, and the result is filtered
        to the user plus those whitelisted orgs (repos from other orgs the
        user happens to be a member of are dropped)."""
        affiliation = "owner,organization_member" if self.include_orgs else "owner"
        repos: list[dict] = []
        page = 1
        while True:
            r = self.session.get(
                f"{GITHUB_API}/user/repos",
                params={
                    "per_page": 100,
                    "page": page,
                    "sort": "updated",
                    "affiliation": affiliation,
                    "visibility": "all",
                },
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
        repos = [r for r in repos if not r.get("fork")]
        if self.include_orgs:
            allowed = {self.user.lower(), *(o.lower() for o in self.include_orgs)}
            repos = [
                r for r in repos
                if r.get("owner", {}).get("login", "").lower() in allowed
            ]
        return repos

    def fetch_repo_languages(self, owner: str, repo: str) -> dict[str, int]:
        r = self.session.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/languages", timeout=15
        )
        r.raise_for_status()
        return r.json()

    def fetch_total_commits(self, created_at: str, today: date) -> int:
        """All-time commits (public + private) since `created_at`.

        contributionsCollection only accepts a 1-year window, so we chunk the
        full lifetime into 365-day date slices (inclusive, non-overlapping)
        and sum totalCommitContributions + restrictedContributionsCount for
        each. The private count is included only if the requesting token can
        see those contributions, which the dashboard's classic PAT can."""
        start_date = date.fromisoformat(created_at[:10])
        total = 0
        window_start = start_date
        while window_start <= today:
            window_end = min(window_start + timedelta(days=365), today)
            r = self.session.post(
                GITHUB_GRAPHQL,
                json={
                    "query": (
                        "query($login: String!, $from: DateTime!, $to: DateTime!) {"
                        "  user(login: $login) {"
                        "    contributionsCollection(from: $from, to: $to) {"
                        "      totalCommitContributions"
                        "      restrictedContributionsCount"
                        "    }"
                        "  }"
                        "}"
                    ),
                    "variables": {
                        "login": self.user,
                        "from": f"{window_start}T00:00:00Z",
                        "to": f"{window_end}T23:59:59Z",
                    },
                },
                timeout=20,
            )
            r.raise_for_status()
            cc = r.json()["data"]["user"]["contributionsCollection"]
            total += cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
            if window_end >= today:
                break
            window_start = window_end + timedelta(days=1)
        return total

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
            n
            for langs in repo_langs.values()
            for name, n in langs.items()
            if name not in EXCLUDED_LANGUAGES
        )

        contrib = self.fetch_contributions(today=today)
        total_commits = self.fetch_total_commits(
            created_at=user["created_at"], today=today
        )
        activity = extract_activity(contrib["days"], today=today, window=60)
        activity_avg = sum(activity) / len(activity) if activity else 0.0
        activity_peak = max(activity) if activity else 0
        # Streak = consecutive active days ending today (or yesterday, if no
        # contributions have landed today yet — common when CI runs in UTC
        # while the user is still on the previous calendar day locally).
        streak = 0
        days_reversed = list(reversed(activity))
        if days_reversed and days_reversed[0] == 0:
            days_reversed = days_reversed[1:]
        for v in days_reversed:
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
            # `public_repos` retains its historical name but now reflects
            # all owned non-fork repos visible to the token (public + private).
            "public_repos": len(repos),
            "total_stars": sum(r.get("stargazers_count", 0) for r in repos),
            "total_commits": total_commits,
            "total_loc_bytes": total_loc_bytes,
            "languages": languages,
            "activity": activity,
            "activity_avg": float(activity_avg),
            "activity_peak": int(activity_peak),
            "activity_streak": streak,
            "top_repos": top_repos_clean,
        }


EXCLUDED_LANGUAGES = {"Jupyter Notebook"}


def aggregate_languages(
    repo_langs: dict[str, dict[str, int]],
) -> list[tuple[str, float]]:
    """Combine per-repo language bytes into top-5 lowercased + 'other' percentages.

    Languages in EXCLUDED_LANGUAGES are skipped — Jupyter Notebook is excluded
    because its byte count is inflated by base64-encoded cell outputs.
    """
    totals: dict[str, int] = {}
    for langs in repo_langs.values():
        for name, n in langs.items():
            if name in EXCLUDED_LANGUAGES:
                continue
            totals[name] = totals.get(name, 0) + n

    grand = sum(totals.values()) or 1
    sorted_langs = sorted(totals.items(), key=lambda kv: -kv[1])
    top = sorted_langs[:5]
    rest_bytes = sum(n for _, n in sorted_langs[5:])
    out = [(name.lower(), n * 100 / grand) for name, n in top]
    if rest_bytes:
        out.append(("other", rest_bytes * 100 / grand))
    return out


def extract_activity(days: dict[str, int], today: date, window: int = 60) -> list[int]:
    """Return `window` daily counts ending at `today` (oldest first, today last)."""
    out: list[int] = []
    for i in range(window - 1, -1, -1):
        d = today - timedelta(days=i)
        out.append(days.get(d.isoformat(), 0))
    return out
