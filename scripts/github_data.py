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
