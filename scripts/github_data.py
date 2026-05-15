"""GitHub API fetchers for the dashboard generator."""

import requests
from datetime import date, timedelta


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

    def fetch_repo_languages(self, owner: str, repo: str) -> dict[str, int]:
        r = self.session.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/languages", timeout=15
        )
        r.raise_for_status()
        return r.json()

    def fetch_total_commits(self) -> int:
        """All-time public commit count for the user, via the search API."""
        r = self.session.get(
            f"{GITHUB_API}/search/commits",
            params={"q": f"author:{self.user}", "per_page": 1},
            headers={"Accept": "application/vnd.github.cloak-preview+json"},
            timeout=15,
        )
        r.raise_for_status()
        return r.json()["total_count"]

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
        total_commits = self.fetch_total_commits()
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
            "public_repos": user["public_repos"],
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
