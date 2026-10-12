"""Tests for moosecontainers.config."""

import importlib
import os

from moosecontainers import config


def test_repo_root():
    """The repo root contains the containers and packages files."""
    assert os.path.isfile(
        os.path.join(config.REPO_ROOT, config.CONTAINERS_FILE)
    )
    assert os.path.isfile(os.path.join(config.REPO_ROOT, config.PACKAGES_FILE))


def test_derived():
    """Values derived from the organization and repo."""
    assert config.FULL_REPO == "idaholab/moose-containers"
    assert config.URI_PREFIX == "ghcr.io/idaholab/moose-containers"


def test_workflows_exist():
    """Every workflow template and its output exist in the repo."""
    for template, workflow in config.WORKFLOWS.items():
        assert os.path.isfile(os.path.join(config.REPO_ROOT, template))
        assert os.path.isfile(os.path.join(config.REPO_ROOT, workflow))


def test_repo_root_override(monkeypatch, tmp_path):
    """The repo root can be set from the environment."""
    default = config.REPO_ROOT
    monkeypatch.setenv("MOOSECONTAINERS_REPO_ROOT", str(tmp_path))
    try:
        root = importlib.reload(config).REPO_ROOT
        assert root == str(tmp_path)
        monkeypatch.setenv("MOOSECONTAINERS_REPO_ROOT", "")
        root = importlib.reload(config).REPO_ROOT
        assert root == default
    finally:
        monkeypatch.delenv("MOOSECONTAINERS_REPO_ROOT")
        importlib.reload(config)
