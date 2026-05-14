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


@responses.activate
def test_fetch_total_commits_returns_search_total():
    responses.get(
        "https://api.github.com/search/commits",
        json={"total_count": 9870, "items": []},
        status=200,
    )
    client = GitHubClient(token="t", user="8enji")
    total = client.fetch_total_commits()
    assert total == 9870
    # Verify the query parameter targets the right author
    sent_url = responses.calls[0].request.url
    assert "author%3A8enji" in sent_url or "author:8enji" in sent_url
