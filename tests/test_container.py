"""Tests for moosecontainers.container."""

import datetime

import pytest

from moosecontainers.config import URI_PREFIX
from moosecontainers.container import Container, ContainersException


def make(name="moose-base-os", tags=None, date="20250101", **kwargs):
    """Make a container with defaults."""
    return Container(name, ["1.0"] if tags is None else tags, date, **kwargs)


def make_family() -> tuple[Container, Container, Container]:
    """Make a base -> compiler -> mpi family of containers."""
    base = make("moose-base-os", ["1.0"], dockerfile="os")
    compiler = make("moose-compiler-os-gcc", ["gcc2.0"], dockerfile="gcc")
    compiler.set_from_container(base)
    mpi = make("moose-mpi-os-gcc", ["mpich3.0"], "20250102", dockerfile="mpi")
    mpi.set_from_container(compiler)
    return base, compiler, mpi


def test_exception():
    """The exception message includes the file and container name."""
    e = ContainersException("foo", "bar")
    assert str(e) == "containers.yml: foo: bar"


def test_properties():
    """Basic properties."""
    container = make(release=True, dockerfile="os", build_args={"A": "1"})
    assert container.name == "moose-base-os"
    assert container.date == datetime.date(2025, 1, 1)
    assert container.raw_date == "20250101"
    assert container.release
    assert container.layer == "base"
    assert container.context == "docker/base"
    assert container.file == "docker/base/os/Dockerfile"
    assert container.build_args == {"A": "1"}
    assert container.from_container is None


def test_defaults():
    """Defaults for the optional arguments."""
    container = make()
    assert not container.release
    assert container.build_args == {}


def test_file_not_set():
    """Getting the file without a dockerfile raises."""
    with pytest.raises(ContainersException, match="dockerfile is not set"):
        make().file


@pytest.mark.parametrize("build_args", [["A"], {"A": 1}, {1: "A"}])
def test_bad_build_args(build_args):
    """Build args must map str to str."""
    with pytest.raises(ContainersException, match="must map str to str"):
        make(build_args=build_args)


def test_invalid_date():
    """An unparseable date raises."""
    with pytest.raises(ContainersException, match="date='2025' is invalid"):
        make(date="2025")


def test_future_date():
    """A date in the future raises."""
    future = datetime.date.today() + datetime.timedelta(days=1)
    with pytest.raises(ContainersException, match="is from the future"):
        make(date=future.strftime("%Y%m%d"))


def test_family():
    """Tags, build args and from containers through a family."""
    base, compiler, mpi = make_family()
    assert compiler.from_container is base
    assert mpi.from_container is compiler
    assert base.raw_tag == "1.0-20250101"
    assert compiler.raw_tag == "1.0-gcc2.0-20250101"
    assert mpi.raw_tag == "1.0-gcc2.0-mpich3.0-20250102"
    assert mpi.build_args == {"BUILD_FROM": compiler.uri}


def test_set_from_container_once():
    """The from container can only be set once."""
    _, compiler, _ = make_family()
    with pytest.raises(AssertionError):
        compiler.set_from_container(make())


def test_tag_prefixes():
    """Tag prefix helpers."""
    assert Container.get_pr_tag_prefix(5) == "pr5-"
    assert Container.get_main_tag_prefix() == "main-"


def test_release_tag():
    """A container without a tag, or with a release tag, is a release."""
    container = make()
    expected = f"{URI_PREFIX}/moose-base-os:1.0-20250101"
    assert container.repo == "moose-base-os"
    assert container.tag == "1.0-20250101"
    assert container.uri == expected
    container.set_release_tag()
    assert container.repo == "moose-base-os"
    assert container.uri == expected
    assert container.url == (
        "https://github.com/idaholab/moose-containers/pkgs/container/"
        "moose-containers%2Fmoose-base-os"
    )


def test_pr_tag():
    """A pull request container is in staging with a pr prefix."""
    container = make()
    container.set_pr_tag(5)
    assert container.repo == "staging-moose-base-os"
    assert container.tag == "pr5-1.0-20250101"
    assert container.uri == (
        f"{URI_PREFIX}/staging-moose-base-os:pr5-1.0-20250101"
    )


def test_main_tag():
    """A main container is in staging with a main prefix."""
    container = make()
    container.set_main_tag()
    assert container.repo == "staging-moose-base-os"
    assert container.tag == "main-1.0-20250101"


@pytest.mark.parametrize(
    "first", ["set_main_tag", "set_release_tag", "set_pr_tag"]
)
@pytest.mark.parametrize(
    "second", ["set_main_tag", "set_release_tag", "set_pr_tag"]
)
def test_tag_once(first, second):
    """Only one tag can be set, once."""
    container = make()

    def call(method):
        args = [1] if method == "set_pr_tag" else []
        getattr(container, method)(*args)

    call(first)
    with pytest.raises(AssertionError):
        call(second)
