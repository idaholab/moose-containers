"""Tests for moosecontainers.__main__."""

import runpy
import sys

import pytest

from moosecontainers import cli


def test_module(monkeypatch, capsys):
    """The package can be run with python -m."""
    monkeypatch.setattr(sys, "argv", ["moosecontainers", "--help"])
    with pytest.raises(SystemExit) as e:
        runpy.run_module("moosecontainers", run_name="__main__")
    assert e.value.code == 0
    assert capsys.readouterr().out.startswith("usage: moosecontainers")


def test_module_import(monkeypatch):
    """Importing the module entry point does not run anything."""
    monkeypatch.setattr(cli, "main", lambda: pytest.fail("ran main"))
    runpy.run_module("moosecontainers.__main__", run_name="imported")
