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
def test_fetch_repos_excludes_forks_and_uses_auth_scoped_endpoint():
    responses.get(
        "https://api.github.com/user/repos",
        json=[
            {"name": "a", "fork": False, "stargazers_count": 10, "language": "Python", "private": False},
            {"name": "b", "fork": True, "stargazers_count": 5, "language": "Go", "private": False},
            {"name": "c", "fork": False, "stargazers_count": 3, "language": "Rust", "private": True},
        ],
        status=200,
    )
    client = GitHubClient(token="t", user="8enji")
    repos = client.fetch_repos()
    assert [r["name"] for r in repos] == ["a", "c"]
    # Private repos are kept (only forks are filtered out)
    assert any(r["private"] for r in repos)


@responses.activate
def test_fetch_repos_sends_auth_header():
    responses.get(
        "https://api.github.com/user/repos",
        json=[],
        status=200,
    )
    client = GitHubClient(token="my-token", user="8enji")
    client.fetch_repos()
    assert responses.calls[0].request.headers["Authorization"] == "Bearer my-token"
    # And we asked for both visibilities
    assert "visibility=all" in responses.calls[0].request.url


@responses.activate
def test_fetch_repos_default_keeps_affiliation_owner_only():
    """With no whitelist, the affiliation stays owner-only (current behavior)."""
    responses.get(
        "https://api.github.com/user/repos",
        json=[],
        status=200,
    )
    client = GitHubClient(token="t", user="8enji")
    client.fetch_repos()
    url = responses.calls[0].request.url
    assert "affiliation=owner" in url
    assert "organization_member" not in url


@responses.activate
def test_fetch_repos_includes_whitelisted_org_and_excludes_others():
    """A whitelisted org's repos are kept; the affiliation is broadened to pull
    them in, and repos from non-whitelisted orgs are filtered out."""
    responses.get(
        "https://api.github.com/user/repos",
        json=[
            {"name": "static-rs", "owner": {"login": "8enji"}, "fork": False},
            {"name": "veil", "owner": {"login": "getveil"}, "fork": False},
            {"name": "elsewhere", "owner": {"login": "someorg"}, "fork": False},
        ],
        status=200,
    )
    client = GitHubClient(token="t", user="8enji", include_orgs=["getveil"])
    repos = client.fetch_repos()
    assert sorted(r["name"] for r in repos) == ["static-rs", "veil"]
    # Affiliation broadened so org-member repos are returned by the API.
    assert "organization_member" in responses.calls[0].request.url


@responses.activate
def test_fetch_repos_org_whitelist_is_case_insensitive():
    responses.get(
        "https://api.github.com/user/repos",
        json=[
            {"name": "veil", "owner": {"login": "getveil"}, "fork": False},
        ],
        status=200,
    )
    client = GitHubClient(token="t", user="8enji", include_orgs=["GetVeil"])
    repos = client.fetch_repos()
    assert [r["name"] for r in repos] == ["veil"]


@responses.activate
def test_fetch_total_commits_sums_public_and_private_across_years():
    # Account created roughly 2 years before "today", so the lifetime spans
    # two yearly windows. Each window returns its own public + private split.
    responses.post(
        "https://api.github.com/graphql",
        json={"data": {"user": {"contributionsCollection": {
            "totalCommitContributions": 400,
            "restrictedContributionsCount": 600,
        }}}},
        status=200,
    )
    responses.post(
        "https://api.github.com/graphql",
        json={"data": {"user": {"contributionsCollection": {
            "totalCommitContributions": 200,
            "restrictedContributionsCount": 100,
        }}}},
        status=200,
    )
    client = GitHubClient(token="t", user="8enji")
    from datetime import date
    total = client.fetch_total_commits(
        created_at="2024-05-15T00:00:00Z", today=date(2026, 5, 15)
    )
    # (400 + 600) + (200 + 100) = 1300
    assert total == 1300
    # Two GraphQL POSTs, one per yearly window
    posts = [c for c in responses.calls if c.request.method == "POST"]
    assert len(posts) == 2
