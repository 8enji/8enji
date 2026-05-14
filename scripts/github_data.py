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

    def fetch_repo_languages(self, owner: str, repo: str) -> dict[str, int]:
        r = self.session.get(
            f"{GITHUB_API}/repos/{owner}/{repo}/languages", timeout=15
        )
        r.raise_for_status()
        return r.json()


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
