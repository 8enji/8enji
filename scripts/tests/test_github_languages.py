import responses

from scripts.github_data import GitHubClient, aggregate_languages


@responses.activate
def test_fetch_repo_languages():
    responses.get(
        "https://api.github.com/repos/8enji/foo/languages",
        json={"TypeScript": 1000, "Python": 500},
        status=200,
    )
    client = GitHubClient(token="t", user="8enji")
    langs = client.fetch_repo_languages("8enji", "foo")
    assert langs == {"TypeScript": 1000, "Python": 500}


def test_aggregate_languages_sums_top_five_plus_other():
    repo_langs = {
        "a": {"TypeScript": 4200, "Python": 1000},
        "b": {"Python": 1300, "Go": 1400, "Rust": 1100},
        "c": {"Lua": 600, "Shell": 200, "Vim Script": 200},
    }
    result = aggregate_languages(repo_langs)
    names = [n for n, _ in result]
    assert names[0] == "typescript"
    assert "other" in names
    # Sum should be ~100%
    total_pct = sum(p for _, p in result)
    assert 99.0 <= total_pct <= 101.0


def test_aggregate_languages_returns_at_most_six_rows():
    repo_langs = {"r": {f"L{i}": 1000 for i in range(20)}}
    result = aggregate_languages(repo_langs)
    assert len(result) <= 6
