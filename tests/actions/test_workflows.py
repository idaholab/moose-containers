"""Tests for moosecontainers.actions.workflows."""

import os

import pytest

from moosecontainers.actions.workflows import (
    WorkflowsException,
    action_versions,
    render,
)
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


def test_action_versions(repo):
    """Versions come from the workflows and actions, but not build.yml."""
    repo.write(
        ".github/workflows/other.yml",
        "steps:\n"
        "  - uses: actions/checkout@v7\n"
        "  - name: Local\n"
        "    uses: ./.github/actions/build\n"
        "  - uses: astral-sh/setup-uv@v1.2.3 # comment\n",
    )
    repo.write(
        ".github/actions/build/action.yml",
        "    uses: docker/login-action@v4\n    uses: actions/checkout@v7\n",
    )
    repo.write(WORKFLOW, "uses: actions/checkout@v1\n")
    assert action_versions() == {
        "actions/checkout": "v7",
        "astral-sh/setup-uv": "v1.2.3",
        "docker/login-action": "v4",
    }


def test_action_versions_differ(repo):
    """An action used at two versions raises."""
    repo.write(".github/workflows/a.yml", "uses: actions/checkout@v6\n")
    repo.write(".github/workflows/b.yml", "uses: actions/checkout@v7\n")
    with pytest.raises(WorkflowsException, match="both v6 and v7"):
        action_versions()


def test_render_action(repo):
    """The template gets actions at their versions."""
    repo.write(".github/workflows/other.yml", "uses: actions/checkout@v7\n")
    repo.write(TEMPLATE, '[[ action("actions/checkout") ]]\n')
    assert render(TEMPLATE) == "actions/checkout@v7\n"


def test_render_action_unknown(repo):
    """An action that isn't used elsewhere raises."""
    repo.write(TEMPLATE, '[[ action("actions/checkout") ]]\n')
    with pytest.raises(WorkflowsException, match="version is unknown"):
        render(TEMPLATE)


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
