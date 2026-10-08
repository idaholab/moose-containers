"""Tests for moosecontainers.actions.delete_untagged."""

import pytest

from moosecontainers.actions.delete_untagged import condition
from moosecontainers.cli import main, parse_args
from moosecontainers.github import GitHubContainer


def make(tags: list[str]) -> GitHubContainer:
    """Make a GitHub container with the given tags."""
    return GitHubContainer(name="n", id=1, tags=tags, sha="s", uri="u")


def test_parser():
    """The github token is required."""
    args = parse_args(["delete_untagged", "--github-token", "t", "--dry-run"])
    assert args.dry_run
    with pytest.raises(SystemExit):
        parse_args(["delete_untagged"])


def test_condition():
    """Only untagged containers are deleted."""
    assert condition(make([]))
    assert not condition(make(["a"]))


def test_run(repo, registry):
    """Delete the untagged images."""
    for repo_name in ["base-os", "compiler-os-gcc", "mpi-os-gcc"]:
        registry.add_version(f"staging-moose-{repo_name}", 1, [])
        registry.add_version(f"staging-moose-{repo_name}", 2, ["a"])
    main(["delete_untagged", "--github-token", "t"])
    assert {id for _, id in registry.deleted} == {1}
    assert len(registry.deleted) == 3


def test_run_missing_repos(repo, registry):
    """Missing repos fail."""
    with pytest.raises(SystemExit):
        main(["delete_untagged", "--github-token", "t"])
