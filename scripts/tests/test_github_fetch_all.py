from datetime import date

import responses

from scripts.github_data import GitHubClient


@responses.activate
def test_fetch_all_composes_dashboard_data():
    responses.get(
        "https://api.github.com/users/8enji",
        json={
            "login": "8enji",
            "followers": 89,
            "public_repos": 42,
            "created_at": "2025-05-14T00:00:00Z",
        },
        status=200,
    )
    responses.get(
        "https://api.github.com/user/repos",
        json=[
            {"name": "static-rs", "owner": {"login": "8enji"}, "fork": False,
             "stargazers_count": 84, "language": "Rust", "private": False},
            {"name": "tinybuf", "owner": {"login": "8enji"}, "fork": False,
             "stargazers_count": 51, "language": "Go", "private": False},
            {"name": "dotfiles", "owner": {"login": "8enji"}, "fork": False,
             "stargazers_count": 37, "language": "Lua", "private": True},
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
    # The contributions calendar (per-day) and the all-time commits sum both
    # hit the GraphQL endpoint. The responses library matches POSTs in order.
    # Call order: fetch_contributions (calendar) then fetch_total_commits (1
    # yearly window since created_at is ~1 year before today).
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
    responses.post(
        "https://api.github.com/graphql",
        json={"data": {"user": {"contributionsCollection": {
            "totalCommitContributions": 3128,
            "restrictedContributionsCount": 1000,
        }}}},
        status=200,
    )

    client = GitHubClient(token="t", user="8enji")
    data = client.fetch_all(today=date(2026, 5, 14))

    assert data["followers"] == 89
    # public_repos field now reflects all owned non-fork repos (including private)
    assert data["public_repos"] == 3
    assert data["total_stars"] == 84 + 51 + 37
    # total_commits = sum of (totalCommitContributions + restrictedContributionsCount)
    # across yearly windows from created_at to today (= 3128 + 1000 here)
    assert data["total_commits"] == 4128
    assert data["total_loc_bytes"] == 140000
    assert len(data["activity"]) == 60
    assert data["activity"][-1] == 12
    assert data["top_repos"][0]["name"] == "static-rs"
    assert isinstance(data["activity_avg"], float)
    assert data["activity_peak"] >= 12
