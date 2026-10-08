"""Tests for moosecontainers.actions.post_release."""

from moosecontainers.actions import post_release
from moosecontainers.cli import main, parse_args


def test_parser():
    """Parse the arguments."""
    args = parse_args(["post_release", "--github-token", "t"])
    assert args.github_token == "t"


def test_run(monkeypatch):
    """Run the post action for a release."""
    calls = []
    monkeypatch.setattr(
        post_release, "post_action", lambda *a, **k: calls.append((a, k))
    )
    main(["post_release", "--github-token", "t"])
    assert calls == [(("t",), {"release": True})]
