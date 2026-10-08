"""Tests for moosecontainers.actions.prepare_push."""

from moosecontainers.cli import main, parse_args


def test_parser():
    """Parse the arguments."""
    args = parse_args(["prepare_push", "main"])
    assert (args.base_ref, args.github_token) == ("main", None)


def test_run(repo, capsys):
    """Run against the current commit."""
    main(["prepare_push", "HEAD"])
    out = capsys.readouterr().out
    assert "No containers to build" in out
    assert "staging-moose-base-os:main-1.0-20250101" in out
