"""Tests for moosecontainers.delete."""

import pytest

from moosecontainers.config import URI_PREFIX
from moosecontainers.delete import delete_containers

REPOS = [
    "staging-moose-base-os",
    "staging-moose-compiler-os-gcc",
    "staging-moose-mpi-os-gcc",
]
"""The staging container repos in the test repo."""


def setup_versions(registry):
    """Add package versions to every staging repo."""
    for repo in REPOS:
        registry.add_version(repo, 1, ["latest"])
        registry.add_version(repo, 2, [])
        registry.add_version(repo, 3, ["pr5-foo"])


def always(_) -> bool:
    """Delete everything."""
    return True


def test_delete(repo, registry, capsys):
    """Delete everything (except latest) that matches."""
    setup_versions(registry)
    delete_containers(always, "token", False, False)
    assert registry.deleted == [(r, i) for r in REPOS for i in [2, 3]]

    out = capsys.readouterr().out
    sha2, sha3 = f"sha256:{2:064x}", f"sha256:{3:064x}"
    base = f"{URI_PREFIX}/staging-moose-base-os"
    assert f"Checking {REPOS[0]}...\n" in out
    assert f"  Deleting {base}@{sha2} id=2...\n" in out
    assert f"  Deleting {base}:pr5-foo@{sha3} id=3...\n" in out
    assert out.endswith("\nDeleted 6 image(s)\n")


def test_condition(repo, registry):
    """Only delete what matches the condition."""
    setup_versions(registry)
    delete_containers(lambda c: c.id == 3, "token", False, False)
    assert registry.deleted == [(r, 3) for r in REPOS]


def test_dry_run(repo, registry, capsys):
    """A dry run deletes nothing."""
    setup_versions(registry)
    delete_containers(always, "token", True, False)
    assert registry.deleted == []
    out = capsys.readouterr().out
    assert f"  Would delete {URI_PREFIX}/staging-moose-base-os@" in out
    assert out.endswith("\nDeleted 0 image(s)\n")


def test_multiple_tags(repo, registry):
    """A container with multiple tags (and not latest) is unexpected."""
    registry.add_version(REPOS[0], 1, ["a", "b"])
    with pytest.raises(AssertionError, match="one or no tags"):
        delete_containers(always, "token", False, False)


def test_missing_repos(repo, registry, capsys):
    """Missing container repos fail unless allowed."""
    registry.add_version(REPOS[0], 2, [])
    with pytest.raises(SystemExit):
        delete_containers(always, "token", False, False)
    out = capsys.readouterr().out
    assert "  moose-compiler-os-gcc does not exist\n" in out
    assert out.endswith(f"do not exist:\n\n{REPOS[1]}\n{REPOS[2]}\n")

    delete_containers(always, "token", False, True)
    assert registry.deleted == [(REPOS[0], 2), (REPOS[0], 2)]
