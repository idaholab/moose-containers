"""Tests for moosecontainers.post."""

import pytest

from moosecontainers.config import URI_PREFIX
from moosecontainers.post import post_action

BASE = "moose-base-os:1.0-20250101"
COMPILER = "moose-compiler-os-gcc:1.0-gcc2.0-20250101"
MPI = "moose-mpi-os-gcc:1.0-gcc2.0-mpich3.0-20250101"


def uri(name_tag: str, prefix: str | None = None) -> str:
    """Get the URI for a container, in staging with the given prefix."""
    if prefix is None:
        return f"{URI_PREFIX}/{name_tag}"
    name, tag = name_tag.split(":")
    return f"{URI_PREFIX}/staging-{name}:{prefix}{tag}"


def test_push(repo, registry, capsys):
    """After a push, every main container exists."""
    for v in [BASE, COMPILER, MPI]:
        registry.add(uri(v, "main-"))
    post_action("token")
    out = capsys.readouterr().out
    assert f"Checking {BASE}...\n  {uri(BASE, 'main-')}... exists\n" in out


def test_push_missing(repo, registry, capsys):
    """After a push, a missing main container fails."""
    registry.add(uri(BASE, "main-"))
    registry.add(uri(MPI, "main-"))
    with pytest.raises(SystemExit) as e:
        post_action("token")
    assert e.value.code == 1
    out = capsys.readouterr().out
    assert f"  {uri(COMPILER, 'main-')}... does not exist\n" in out
    assert out.endswith(f"registry:\n\n  - {COMPILER}\n")


def test_pr(repo, registry, capsys):
    """After a pull request, each container exists as a PR or main image."""
    registry.add(uri(BASE, "main-"))
    registry.add(uri(COMPILER, "pr5-"))
    registry.add(uri(MPI, "pr5-"))
    post_action("token", pr=5)
    out = capsys.readouterr().out
    assert (
        f"  {uri(BASE, 'pr5-')}... does not exist\n"
        f"  {uri(BASE, 'main-')}... exists\n"
    ) in out
    assert f"  {uri(COMPILER, 'pr5-')}... exists\n" in out
    assert uri(COMPILER, "main-") not in out


def test_pr_missing(repo, registry):
    """After a pull request, a container in neither fails."""
    with pytest.raises(SystemExit):
        post_action("token", pr=5)


def test_release(repo, registry, capsys):
    """After a release, every release container exists."""
    registry.add(uri(BASE))
    registry.add(uri(MPI))
    post_action("token", release=True)
    out = capsys.readouterr().out
    assert f"  {uri(BASE)}... exists\n" in out
    assert "compiler" not in out
    assert "main-" not in out


def test_release_missing(repo, registry, capsys):
    """After a release, a missing release container fails."""
    registry.add(uri(BASE))
    registry.add(uri(MPI, "main-"))
    with pytest.raises(SystemExit):
        post_action("token", release=True)
    assert capsys.readouterr().out.endswith(f"registry:\n\n  - {MPI}\n")
