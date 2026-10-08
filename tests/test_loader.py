"""Tests for moosecontainers.loader."""

import subprocess

import jinja2
import pytest

from moosecontainers import config, loader
from moosecontainers.container import ContainersException


def test_git_show(repo):
    """git_show shows a file at a previous reference."""
    sha = repo.git("rev-parse", "HEAD").strip()
    repo.write_packages({"os": "9.9"})
    repo.commit()
    assert loader.git_show(config.PACKAGES_FILE, "HEAD") == 'os: "9.9"\n'
    assert 'os: "1.0"' in loader.git_show(config.PACKAGES_FILE, sha)


def test_git_show_missing(repo):
    """git_show raises for an unknown reference."""
    with pytest.raises(subprocess.CalledProcessError):
        loader.git_show(config.PACKAGES_FILE, "doesnotexist")


def test_load_containers_string():
    """Load containers from a template string."""
    template = """
a:
  dockerfile: a
  build-args:
    V: "{{ package("v") }}"
  tags: ["{{ package("v") }}"]
  date: "20250101"
b:
  from: a
  tags: ["b"]
  date: "20250102"
  release: true
"""
    containers = loader.load_containers(template, {"v": "1"})
    assert list(containers) == ["a", "b"]
    a, b = containers["a"], containers["b"]
    assert a.name == "moose-a"
    assert a.build_args == {"V": "1"}
    assert b.from_container is a
    assert b.release
    assert b.raw_tag == "1-b-20250102"


def test_load_containers_loader(repo):
    """Load containers from a file system loader."""
    containers = loader.load_containers(
        jinja2.FileSystemLoader(repo.root),
        {"os": "a", "gcc": "b", "mpich": "c"},
    )
    assert containers["mpi-os-gcc"].raw_tag == "a-gccb-mpichc-20250101"


def test_load_containers_unknown_package():
    """An unknown package raises."""
    with pytest.raises(KeyError, match="Unknown package foo"):
        loader.load_containers('a: "{{ package("foo") }}"', {})


def test_load_containers_unknown_from():
    """An unknown from container raises."""
    template = 'a:\n  from: b\n  tags: []\n  date: "20250101"\n'
    with pytest.raises(ContainersException, match="from container b not"):
        loader.load_containers(template, {})


def test_load_current(repo):
    """Load the current containers and packages."""
    containers, packages = loader.load_current()
    assert list(containers) == ["base-os", "compiler-os-gcc", "mpi-os-gcc"]
    assert packages == {"os": "1.0", "gcc": "2.0", "mpich": "3.0"}


def test_load_current_missing_dockerfile(repo):
    """A missing Dockerfile raises for the current containers."""
    repo.write_containers(
        'base-foo:\n  dockerfile: foo\n  tags: []\n  date: "20250101"\n'
    )
    with pytest.raises(ContainersException, match="Dockerfile does not exist"):
        loader.load_current()


def test_load_previous(repo):
    """Load the containers and packages at a previous reference."""
    sha = repo.git("rev-parse", "HEAD").strip()
    repo.write_packages({"os": "1.1", "gcc": "2.0", "mpich": "3.0"})
    repo.commit()
    containers, packages = loader.load_previous(sha)
    assert packages["os"] == "1.0"
    assert containers["base-os"].raw_tag == "1.0-20250101"
