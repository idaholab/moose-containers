"""Tests for moosecontainers.actions.prepare_release."""

import json

import pytest

from moosecontainers.cli import main, parse_args
from moosecontainers.config import URI_PREFIX

BASE = f"{URI_PREFIX}/moose-base-os:1.0-20250101"
MPI = f"{URI_PREFIX}/moose-mpi-os-gcc:1.0-gcc2.0-mpich3.0-20250101"


def main_uri(uri: str) -> str:
    """Convert a release URI to its main URI."""
    name, tag = uri.removeprefix(f"{URI_PREFIX}/").split(":")
    return f"{URI_PREFIX}/staging-{name}:main-{tag}"


def releases(capsys) -> list:
    """Get the releases output from what was printed."""
    out = capsys.readouterr().out
    line = next(v for v in out.splitlines() if v.startswith("releases="))
    return json.loads(line.removeprefix("releases="))


def test_parser():
    """The github token is required."""
    assert parse_args(["prepare_release", "--github-token", "t"]).github_token
    with pytest.raises(SystemExit):
        parse_args(["prepare_release"])


def test_run(repo, registry, capsys):
    """Release containers that aren't released and whose main image exists."""
    registry.add(BASE)
    registry.add(main_uri(MPI))
    main(["prepare_release", "--github-token", "t"])
    assert releases(capsys) == [
        {"name": "mpi-os-gcc", "from": main_uri(MPI), "to": MPI}
    ]


def test_run_nothing(repo, registry, capsys):
    """Nothing to release."""
    registry.add(BASE)
    registry.add(MPI)
    main(["prepare_release", "--github-token", "t"])
    out = capsys.readouterr().out
    assert "No containers to release" in out
    assert "releases=[]" in out


def test_run_missing_main(repo, registry, capsys):
    """A release without its main image fails."""
    registry.add(BASE)
    with pytest.raises(SystemExit) as e:
        main(["prepare_release", "--github-token", "t"])
    assert e.value.code == 1
    assert f"::error::Main container {main_uri(MPI)} does not exist" in (
        capsys.readouterr().out
    )
