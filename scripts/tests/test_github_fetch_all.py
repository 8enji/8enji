from datetime import date

import responses

from scripts.github_data import GitHubClient


@responses.activate
def test_fetch_all_composes_dashboard_data():
    responses.get(
        "https://api.github.com/users/8enji",
        json={"login": "8enji", "followers": 89, "public_repos": 42},
        status=200,
    )
    responses.get(
        "https://api.github.com/users/8enji/repos",
        json=[
            {"name": "static-rs", "owner": {"login": "8enji"}, "fork": False,
             "stargazers_count": 84, "language": "Rust"},
            {"name": "tinybuf", "owner": {"login": "8enji"}, "fork": False,
             "stargazers_count": 51, "language": "Go"},
            {"name": "dotfiles", "owner": {"login": "8enji"}, "fork": False,
             "stargazers_count": 37, "language": "Lua"},
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

    client = GitHubClient(token="t", user="8enji")
    data = client.fetch_all(today=date(2026, 5, 14))

    assert data["followers"] == 89
    assert data["public_repos"] == 42
    assert data["total_stars"] == 84 + 51 + 37
    assert data["total_commits"] == 3128
    assert data["total_loc_bytes"] == 140000
    assert len(data["activity"]) == 60
    assert data["activity"][-1] == 12
    assert data["top_repos"][0]["name"] == "static-rs"
    assert isinstance(data["activity_avg"], float)
    assert data["activity_peak"] >= 12
