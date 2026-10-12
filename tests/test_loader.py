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
    """An unknown from container raises with its location."""
    template = 'a:\n  from: b\n  tags: []\n  date: "20250101"\n'
    with pytest.raises(loader.ConfigError) as e:
        loader.load_containers(template, {})
    assert str(e.value) == "containers.yml:2:9: a.from: container b not found"


@pytest.mark.parametrize(
    "contents, message",
    [
        ("", "containers.yml: Input should be a valid dictionary"),
        (
            "a: 1\n",
            "containers.yml:1:4: a: Input should be a valid dictionary"
            " or instance of ContainerConfig",
        ),
        (
            'a:\n  tags: ["x", 1]\n  date: "20250101"\n',
            "containers.yml:2:15: a.tags.1: Input should be a valid string",
        ),
        (
            'a:\n  tags: []\n  date: "20250101"\n  build-args: {1: "x"}\n',
            "containers.yml:4:16: a.build-args.1: Input should be a valid"
            " string",
        ),
        (
            'a:\n  tags: []\n  date: "20250101"\n  release: "yes"\n',
            "containers.yml:4:12: a.release: Input should be a valid boolean",
        ),
        (
            'a:\n  tags: []\n  date: "20250101"\n  foo: 1\n',
            "containers.yml:4:3: a.foo: Extra inputs are not permitted",
        ),
        (
            "a:\n  tags: []\n",
            "containers.yml:2:3: a.date: Field required",
        ),
        (
            'a:\n  tags: []\n  date: "2025"\n',
            "containers.yml:3:9: a.date: Value error, '2025' is not a valid"
            " YYYYMMDD date",
        ),
        (
            'a:\n  tags: []\n  date: "99990101"\n',
            "containers.yml:3:9: a.date: Value error, '99990101' is from the"
            " future",
        ),
        (
            "a:\n  tags: []\n  date: 20250101\n",
            "containers.yml:3:9: a.date: Input should be a valid string",
        ),
        (
            'a/b:\n  tags: []\n  date: "20250101"\n',
            "containers.yml:1:1: a/b: String should match pattern",
        ),
        (
            'a:\n  tags: ["x y"]\n  date: "20250101"\n',
            "containers.yml:2:10: a.tags.0: String should match pattern",
        ),
        (
            'a:\n  dockerfile: ../b\n  tags: []\n  date: "20250101"\n',
            "containers.yml:2:15: a.dockerfile: String should match pattern",
        ),
        (
            'a:\n  tags: []\n  date: "20250101"\n  build-args: {"A B": "x"}\n',
            "containers.yml:4:16: a.build-args.A B: String should match"
            " pattern",
        ),
        (
            'a:\n  tags: []\n  date: "20250101"\n  build-args: {A: "$(x)"}\n',
            "containers.yml:4:19: a.build-args.A: String should match pattern",
        ),
        (
            'a:\n  from: "-b"\n  tags: []\n  date: "20250101"\n',
            "containers.yml:2:9: a.from: String should match pattern",
        ),
    ],
)
def test_load_containers_invalid(contents, message):
    """Invalid containers raise with their location."""
    with pytest.raises(loader.ConfigError) as e:
        loader.load_containers(contents, {})
    assert str(e.value).startswith(message)


def test_load_containers_sandboxed():
    """The template can't reach unsafe attributes."""
    template = 'a: "{{ package.__globals__.keys() }}"'
    with pytest.raises(jinja2.exceptions.SecurityError):
        loader.load_containers(template, {})


def test_load_containers_invalid_multiple():
    """Each error is reported on its own line."""
    template = 'a:\n  tags: [1]\n  date: "20250101"\n  foo: 1\n'
    with pytest.raises(loader.ConfigError) as e:
        loader.load_containers(template, {}, "foo.yml")
    assert str(e.value).splitlines() == [
        "foo.yml:2:10: a.tags.0: Input should be a valid string",
        "foo.yml:4:3: a.foo: Extra inputs are not permitted",
    ]


def test_load_containers_invalid_yaml():
    """Invalid YAML raises with its location."""
    with pytest.raises(loader.ConfigError, match='"containers.yml", line 1'):
        loader.load_containers("a: [1\n", {})


def test_load_packages():
    """Load packages."""
    assert loader.load_packages('a: "1"\nb: "2"\n', "p.yml") == {
        "a": "1",
        "b": "2",
    }


@pytest.mark.parametrize("contents", ['a/b: "1"\n', 'a: "1 2"\n'])
def test_load_packages_unsafe(contents):
    """Package names and values are limited to safe characters."""
    with pytest.raises(loader.ConfigError, match="String should match"):
        loader.load_packages(contents, "p.yml")


def test_load_packages_invalid():
    """Packages that aren't strings raise with their location."""
    with pytest.raises(loader.ConfigError) as e:
        loader.load_packages('a: "1"\nb: 1.0\n', "p.yml")
    assert str(e.value) == "p.yml:2:4: b: Input should be a valid string"


def test_find_node_key():
    """Key errors locate the key, not the value."""
    _, locate = loader.load_yaml('a: "1"\n', "p.yml", loader.PackagesConfig)
    assert locate(("a", "[key]")) == "p.yml:1:1"
    assert locate(("a",)) == "p.yml:1:4"
    assert locate(("b",)) == "p.yml:1:1"
    assert locate(("a", "b")) == "p.yml:1:4"


def test_find_node_duplicate_key():
    """Duplicate keys locate the last one, which is the one used."""
    _, locate = loader.load_yaml(
        'a: "1"\na: "2"\n', "p.yml", loader.PackagesConfig
    )
    assert locate(("a",)) == "p.yml:2:4"


def test_load_current_invalid_packages(repo):
    """Invalid current packages raise with their location."""
    repo.write(config.PACKAGES_FILE, "os: 1.0\n")
    with pytest.raises(loader.ConfigError, match="packages.yml:1:5: os:"):
        loader.load_current()


def test_load_previous_invalid(repo):
    """Errors in a previous reference include the reference."""
    repo.write_containers('a:\n  tags: []\n  date: "2025"\n')
    sha = repo.commit()
    with pytest.raises(loader.ConfigError) as e:
        loader.load_previous(sha)
    assert str(e.value).startswith(f"{sha}:containers.yml:3:9: a.date:")


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
