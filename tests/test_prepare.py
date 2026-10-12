"""Tests for moosecontainers.prepare."""

import json

import pytest

from moosecontainers.config import URI_PREFIX
from moosecontainers.container import ContainersException
from moosecontainers.prepare import prepare_with_base

BASE = f"{URI_PREFIX}/moose-base-os:1.0-20250101"
"""The release URI for base-os."""

MPI = f"{URI_PREFIX}/moose-mpi-os-gcc:1.0-gcc2.0-mpich3.0-20250101"
"""The release URI for mpi-os-gcc."""


def staging(uri: str, prefix: str) -> str:
    """Convert a release URI to a staging URI with the given tag prefix."""
    name, tag = uri.removeprefix(f"{URI_PREFIX}/").split(":")
    return f"{URI_PREFIX}/staging-{name}:{prefix}{tag}"


def squash(text: str) -> str:
    """Collapse runs of whitespace, so tables can be checked without padding."""
    return " ".join(text.split())


def outputs(capsys) -> dict:
    """Get the containers output from what was printed."""
    out = capsys.readouterr().out
    line = next(v for v in out.splitlines() if v.startswith("containers="))
    return json.loads(line.removeprefix("containers="))


def test_requires_pr_or_main(repo):
    """Exactly one of pr or main must be given."""
    with pytest.raises(AssertionError):
        prepare_with_base("HEAD")
    with pytest.raises(AssertionError):
        prepare_with_base("HEAD", pr=1, main=True)


def test_pr_no_changes(repo, capsys):
    """Nothing changed in a pull request."""
    result = prepare_with_base("HEAD", pr=5)
    assert "No containers to build" in result
    assert "No packages changed" in result
    assert "No unreleased containers" in result

    info = outputs(capsys)
    assert not any(v["changed"] for v in info.values())
    assert info["base-os"] == {
        "build_args": "OS_VERSION=1.0",
        "changed": False,
        "context": "docker/base",
        "file": "docker/base/os/Dockerfile",
        "uri": staging(BASE, "main-"),
    }
    assert info["compiler-os-gcc"]["build_args"] == (
        f"BUILD_FROM={staging(BASE, 'main-')}\nGCC_VERSION=2.0"
    )


def test_pr_package_changed(repo, capsys):
    """A package change in a pull request builds its containers."""
    base = repo.git("rev-parse", "HEAD").strip()
    repo.write_packages({"os": "1.0", "gcc": "2.1", "mpich": "3.0", "new": "1"})
    repo.commit()

    result = squash(prepare_with_base(base, pr=5))
    assert "| `gcc` | `2.0` | `2.1` |" in result
    assert "| `new` | ADDED | `1` |" in result
    assert "| `mpich`" not in result
    assert "moose-base-os`]" not in result
    assert (
        "| [`moose-compiler-os-gcc`](https://github.com/idaholab/"
        "moose-containers/pkgs/container/moose-containers%2F"
        "staging-moose-compiler-os-gcc) | `main-1.0-gcc2.0-20250101` | "
        f"`{URI_PREFIX}/staging-moose-compiler-os-gcc:"
        "pr5-1.0-gcc2.1-20250101` |"
    ) in result

    info = outputs(capsys)
    assert not info["base-os"]["changed"]
    assert info["compiler-os-gcc"]["changed"]
    assert info["mpi-os-gcc"]["changed"]
    assert info["mpi-os-gcc"]["uri"].endswith(
        ":pr5-1.0-gcc2.1-mpich3.0-20250101"
    )


def test_package_removed(repo):
    """A removed package is in the summary."""
    repo.write_packages({"os": "1.0", "gcc": "2.0", "mpich": "3.0", "old": "1"})
    base = repo.commit()
    repo.write_packages({"os": "1.0", "gcc": "2.0", "mpich": "3.0"})
    repo.commit()

    result = squash(prepare_with_base(base, pr=5))
    assert "| `old` | `1` | REMOVED |" in result


def test_new_container(repo, capsys):
    """A container that is not in the base is built."""
    repo.write_containers(
        repo.read("containers.yml")
        + 'base-new:\n  dockerfile: os\n  tags: ["new"]\n  date: "20250101"\n'
    )
    repo.commit()

    result = squash(prepare_with_base("HEAD~1", pr=5))
    assert "staging-moose-base-new) | | " in result
    assert outputs(capsys)["base-new"]["changed"]


def test_date_moved_back(repo):
    """A date that moved back raises."""
    containers = repo.read("containers.yml")
    repo.write_containers(containers.replace("20250101", "20250102", 1))
    base = repo.commit()
    repo.write_containers(containers)
    repo.commit()

    with pytest.raises(ContainersException, match="date moved back"):
        prepare_with_base(base, pr=5)


def test_main_missing_container(repo, registry, capsys):
    """On main, an unchanged container that doesn't exist is built."""
    registry.add(staging(BASE, "main-"))
    registry.add(BASE)

    result = squash(prepare_with_base("HEAD", main=True, github_token="token"))
    out = capsys.readouterr().out
    assert "staging-moose-base-os:main-1.0-20250101 does not exist" not in out
    assert (
        "::warning::Container "
        f"{URI_PREFIX}/staging-moose-compiler-os-gcc:main-1.0-gcc2.0-20250101"
        " does not exist; building"
    ) in out
    assert "staging-moose-base-os)" not in result
    assert "staging-moose-compiler-os-gcc)" in result

    # base-os is released, mpi-os-gcc is not
    assert f"`{BASE}`" not in result
    assert f"| `moose-mpi-os-gcc` | `{MPI}` |" in result
    assert "moose-base-os`" not in result.split("Unreleased")[1]


def test_pr_with_token(repo, registry, capsys):
    """In a pull request with a token, existence isn't checked for builds."""
    registry.add(BASE)
    registry.add(MPI)
    result = prepare_with_base("HEAD", pr=5, github_token="token")
    assert "No containers to build" in result
    assert "No unreleased containers" in result
    assert "::warning::" not in capsys.readouterr().out
