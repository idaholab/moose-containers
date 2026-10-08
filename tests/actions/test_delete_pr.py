"""Tests for moosecontainers.actions.delete_pr."""

import pytest

from moosecontainers.actions import delete_pr
from moosecontainers.cli import main, parse_args
from moosecontainers.github import GitHubContainer


def make(tags: list[str]) -> GitHubContainer:
    """Make a GitHub container with the given tags."""
    return GitHubContainer(name="n", id=1, tags=tags, sha="s", uri="u")


@pytest.fixture
def run(monkeypatch):
    """Run delete_pr, returning the condition and the remaining arguments."""

    def run(*argv: str):
        calls = []
        monkeypatch.setattr(
            delete_pr, "delete_containers", lambda *a: calls.append(a)
        )
        main(["delete_pr", "5", "--github-token", "t", *argv])
        assert len(calls) == 1
        return calls[0]

    return run


def test_parser():
    """Parse the arguments."""
    args = parse_args(["delete_pr", "5", "--github-token", "t"])
    assert args.pr == 5
    assert not args.only_cache
    assert not args.only_images
    assert not args.allow_missing_repos
    assert not args.dry_run
    with pytest.raises(SystemExit):
        parse_args(["delete_pr", "5"])


def test_only_cache_and_images(capsys):
    """--only-cache and --only-images can't be used together."""
    with pytest.raises(SystemExit):
        main(
            [
                "delete_pr",
                "5",
                "--github-token",
                "t",
                "--only-cache",
                "--only-images",
            ]
        )
    assert "ERROR: Cannot supply" in capsys.readouterr().out


TAGS = [[], ["pr5-cache"], ["pr5-foo"], ["pr6-foo"], ["main-foo"]]
"""Tags to check the conditions against."""


@pytest.mark.parametrize(
    "argv, expected",
    [
        ([], [False, True, True, False, False]),
        (["--only-cache"], [False, True, False, False, False]),
        (["--only-images"], [False, False, True, False, False]),
    ],
)
def test_condition(run, argv, expected):
    """Which images are deleted."""
    condition, *_ = run(*argv)
    assert [condition(make(tags)) for tags in TAGS] == expected


def test_arguments(run):
    """The remaining arguments are passed through."""
    _, *rest = run()
    assert rest == ["t", False, False]
    _, *rest = run("--dry-run", "--allow-missing-repos")
    assert rest == ["t", True, True]
