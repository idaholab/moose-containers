"""Tests for moosecontainers.actions.workflows."""

import os

import pytest

from moosecontainers.actions.workflows import render
from moosecontainers.cli import main, parse_args
from moosecontainers.container import ContainersException

TEMPLATE = ".github/templates/build.yml.j2"
WORKFLOW = ".github/workflows/build.yml"


def test_parser():
    """Parse the arguments."""
    assert not parse_args(["workflows"]).check
    assert parse_args(["workflows", "--check"]).check


def test_render(repo):
    """Render, with parents before children."""
    assert render(TEMPLATE) == (
        "base-os: None\n"
        "compiler-os-gcc: base-os\n"
        "mpi-os-gcc: compiler-os-gcc\n"
        "leaves: mpi-os-gcc\n"
    )


def test_render_order(repo):
    """Children listed before their parents are ordered after them."""
    repo.write_containers(
        "compiler-a:\n  from: base-a\n  dockerfile: gcc\n  tags: []\n"
        '  date: "20250101"\n'
        'base-a:\n  dockerfile: os\n  tags: []\n  date: "20250101"\n'
        'base-b:\n  dockerfile: os\n  tags: []\n  date: "20250101"\n'
    )
    assert render(TEMPLATE) == (
        "base-a: None\nbase-b: None\ncompiler-a: base-a\n"
        "leaves: base-b,compiler-a\n"
    )


def test_render_cycle(repo, monkeypatch):
    """A cycle in the from containers raises."""
    from moosecontainers.actions import workflows

    load_current = workflows.load_current

    def cyclic():
        containers, packages = load_current()
        base = containers["base-os"]
        base._from_container = containers["mpi-os-gcc"]
        return containers, packages

    monkeypatch.setattr(workflows, "load_current", cyclic)
    with pytest.raises(ContainersException, match="form a cycle"):
        render(TEMPLATE)


def test_update(repo, capsys):
    """Write a missing workflow, then it is up to date."""
    assert not os.path.exists(repo.path(WORKFLOW))
    os.makedirs(os.path.dirname(repo.path(WORKFLOW)))
    main(["workflows"])
    assert capsys.readouterr().out == f"Updated {WORKFLOW}\n"
    assert repo.read(WORKFLOW) == render(TEMPLATE)

    main(["workflows", "--check"])
    assert capsys.readouterr().out == f"{WORKFLOW} is up to date\n"


def test_check_out_of_date(repo, capsys):
    """Checking an out of date workflow fails without changing it."""
    repo.write(WORKFLOW, "old")
    with pytest.raises(SystemExit) as e:
        main(["workflows", "--check"])
    assert e.value.code == 1
    out = capsys.readouterr().out
    assert f"out of date:\n\n  {WORKFLOW}\n\nrun:" in out
    assert repo.read(WORKFLOW) == "old"
