"""Tests for moosecontainers.actions.delete_all_prs."""

import pytest

from moosecontainers.actions.delete_all_prs import condition
from moosecontainers.cli import main, parse_args
from moosecontainers.github import GitHubContainer


def make(tags: list[str]) -> GitHubContainer:
    """Make a GitHub container with the given tags."""
    return GitHubContainer(name="n", id=1, tags=tags, sha="s", uri="u")


def test_parser():
    """The github token is required."""
    assert not parse_args(["delete_all_prs", "--github-token", "t"]).dry_run
    with pytest.raises(SystemExit):
        parse_args(["delete_all_prs"])


@pytest.mark.parametrize(
    "tags, expected",
    [
        ([], False),
        (["pr1-foo"], True),
        (["pr123-cache"], True),
        (["main-foo"], False),
        (["prx-foo"], False),
        (["pr1-a", "pr2-b"], False),
    ],
)
def test_condition(tags, expected):
    """Only pull request images are deleted."""
    assert condition(make(tags)) == expected


def test_run(repo, registry):
    """Delete the pull request images."""
    for repo_name in ["base-os", "compiler-os-gcc", "mpi-os-gcc"]:
        registry.add_version(f"staging-moose-{repo_name}", 1, ["pr1-a"])
        registry.add_version(f"staging-moose-{repo_name}", 2, ["main-a"])
    main(["delete_all_prs", "--github-token", "t"])
    assert {id for _, id in registry.deleted} == {1}
