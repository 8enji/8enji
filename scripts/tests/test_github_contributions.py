import json
from datetime import date

import responses

from scripts.github_data import GitHubClient, extract_activity


GRAPHQL_PAYLOAD = {
    "data": {
        "user": {
            "contributionsCollection": {
                "totalCommitContributions": 3128,
                "contributionCalendar": {
                    "weeks": [
                        {
                            "contributionDays": [
                                {"date": "2026-05-12", "contributionCount": 5},
                                {"date": "2026-05-13", "contributionCount": 8},
                                {"date": "2026-05-14", "contributionCount": 12},
                            ]
                        }
                    ]
                },
            }
        }
    }
}


@responses.activate
def test_fetch_contributions():
    responses.post("https://api.github.com/graphql", json=GRAPHQL_PAYLOAD, status=200)
    client = GitHubClient(token="t", user="8enji")
    result = client.fetch_contributions(today=date(2026, 5, 14))
    assert result["total_commits"] == 3128
    assert result["days"][("2026-05-14")] == 12


def test_extract_activity_last_60_days_pads_zeros():
    days = {"2026-05-13": 8, "2026-05-14": 12}
    activity = extract_activity(days, today=date(2026, 5, 14), window=60)
    assert len(activity) == 60
    assert activity[-1] == 12   # today
    assert activity[-2] == 8    # yesterday
    assert activity[0] == 0     # 59 days before today, no data


def test_extract_activity_computes_avg_and_peak():
    days = {"2026-05-13": 8, "2026-05-14": 12}
    activity = extract_activity(days, today=date(2026, 5, 14), window=60)
    from statistics import mean
    avg = mean(activity)
    peak = max(activity)
    assert peak == 12
    assert 0.3 < avg < 0.4
