"""Tests for moosecontainers.actions.post_push."""

from moosecontainers.actions import post_push
from moosecontainers.cli import main, parse_args


def test_parser():
    """Parse the arguments."""
    assert parse_args(["post_push", "--github-token", "t"]).github_token == "t"


def test_run(monkeypatch):
    """Run the post action for a push."""
    calls = []
    monkeypatch.setattr(
        post_push, "post_action", lambda *a, **k: calls.append((a, k))
    )
    main(["post_push", "--github-token", "t"])
    assert calls == [(("t",), {})]
