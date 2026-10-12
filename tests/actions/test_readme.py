"""Tests for moosecontainers.actions.readme."""

import pytest

from moosecontainers.actions.readme import build_releases
from moosecontainers.cli import main, parse_args

URL = "https://github.com/idaholab/moose-containers/pkgs/container"
"""The url for container packages."""


def test_parser():
    """Parse the arguments."""
    assert not parse_args(["readme"]).check
    assert parse_args(["readme", "--check"]).check


def test_build_releases(repo):
    """Build the release table."""
    rows = [" ".join(v.split()) for v in build_releases().splitlines()]
    assert rows[0] == "| container | tag |"
    assert rows[2:] == [
        f"| [`moose-base-os`]({URL}/moose-containers%2Fmoose-base-os) "
        "| `1.0-20250101` |",
        f"| [`moose-mpi-os-gcc`]({URL}/moose-containers%2Fmoose-mpi-os-gcc) "
        "| `1.0-gcc2.0-mpich3.0-20250101` |",
    ]


def test_update(repo, capsys):
    """Update the README, then it is up to date."""
    main(["readme"])
    assert capsys.readouterr().out == "Updated README.md\n"
    contents = repo.read("README.md")
    assert contents == (
        "# test\n\n<!-- releases:start -->\n"
        f"{build_releases()}\n<!-- releases:end -->\n"
    )

    main(["readme", "--check"])
    assert capsys.readouterr().out == "README.md is up to date\n"


def test_check_out_of_date(repo, capsys):
    """Checking an out of date README fails without changing it."""
    before = repo.read("README.md")
    with pytest.raises(SystemExit) as e:
        main(["readme", "--check"])
    assert e.value.code == 1
    assert "release table is out of date" in capsys.readouterr().out
    assert repo.read("README.md") == before


def test_missing_markers(repo, capsys):
    """A README without the markers fails."""
    repo.write("README.md", "# test\n")
    with pytest.raises(SystemExit):
        main(["readme"])
    assert "is missing <!-- releases:start -->" in capsys.readouterr().out
