"""Tests for moosecontainers.arguments."""

import argparse

import pytest

from moosecontainers import arguments


def test_arguments():
    """All of the shared arguments."""
    parser = argparse.ArgumentParser()
    arguments.add_github_token(parser)
    arguments.add_dry_run(parser)
    arguments.add_base_ref(parser)
    arguments.add_pr(parser)
    arguments.add_check(parser, "help")

    args = parser.parse_args(["main", "5"])
    assert args.github_token is None
    assert not args.dry_run
    assert args.base_ref == "main"
    assert args.pr == 5
    assert not args.check

    args = parser.parse_args(
        ["main", "5", "--github-token", "t", "--dry-run", "--check"]
    )
    assert args.github_token == "t"
    assert args.dry_run
    assert args.check


def test_github_token_required():
    """The github token can be required."""
    parser = argparse.ArgumentParser()
    arguments.add_github_token(parser, required=True)
    with pytest.raises(SystemExit):
        parser.parse_args([])
