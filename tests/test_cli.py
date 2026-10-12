"""Tests for moosecontainers.cli."""

import os
import subprocess

import pytest

from moosecontainers import cli
from moosecontainers.config import REPO_ROOT


def test_actions():
    """Every action module is registered under its own name."""
    actions_dir = os.path.join(os.path.dirname(cli.__file__), "actions")
    modules = {
        f.removesuffix(".py")
        for f in os.listdir(actions_dir)
        if f.endswith(".py") and f != "__init__.py"
    }
    assert set(cli.ACTIONS) == modules
    for name, module in cli.ACTIONS.items():
        assert module.__name__ == f"moosecontainers.actions.{name}"


def test_parse_args_requires_action(capsys):
    """An action is required."""
    with pytest.raises(SystemExit):
        cli.parse_args([])


def test_main(monkeypatch):
    """Main runs the given action."""
    calls = []
    monkeypatch.setattr(cli.ACTIONS["readme"], "run", calls.append)
    cli.main(["readme", "--check"])
    assert calls[0].action == "readme"
    assert calls[0].check


def test_script():
    """The moosecontainers script is installed."""
    result = subprocess.run(
        ["moosecontainers", "--help"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert result.stdout.startswith("usage: moosecontainers")
