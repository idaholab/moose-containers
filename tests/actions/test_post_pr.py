"""Tests for moosecontainers.actions.post_pr."""

from moosecontainers.actions import post_pr
from moosecontainers.cli import main, parse_args


def test_parser():
    """Parse the arguments."""
    args = parse_args(["post_pr", "5", "--github-token", "t"])
    assert (args.pr, args.github_token) == (5, "t")


def test_run(monkeypatch):
    """Run the post action for the pull request."""
    calls = []
    monkeypatch.setattr(
        post_pr, "post_action", lambda *a, **k: calls.append((a, k))
    )
    main(["post_pr", "5", "--github-token", "t"])
    assert calls == [(("t",), {"pr": 5})]
