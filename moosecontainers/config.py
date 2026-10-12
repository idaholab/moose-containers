"""Constants for the moose-containers repository."""

import os

REPO_ROOT = os.environ.get("MOOSECONTAINERS_REPO_ROOT") or os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
"""Root path to the repo.

Set MOOSECONTAINERS_REPO_ROOT to read the configuration from another checkout,
such as a pull request from a fork, while running this (trusted) package.
"""

ORG = "idaholab"
"""The GitHub organization."""

REPO = "moose-containers"
"""The GitHub repository."""

FULL_REPO = f"{ORG}/{REPO}"
"""The full GitHub repository (org/repo)."""

URI_PREFIX = f"ghcr.io/{FULL_REPO}"
"""URI prefix for container pushes."""

CONTAINERS_FILE = "containers.yml"
"""The path to the containers.yml file, relative to the repo root."""

PACKAGES_FILE = "packages.yml"
"""The path to the packages.yml file, relative to the repo root."""

GITHUB_API_URL = "https://api.github.com/"
"""The GitHub API url."""

STAGING_PREFIX = "staging-"
"""The prefix used for images stored in a staging repo."""

README_FILE = "README.md"
"""The path to the README.md file, relative to the repo root."""

README_START = "<!-- releases:start -->"
"""Marker for the start of the generated release table in the README."""

README_END = "<!-- releases:end -->"
"""Marker for the end of the generated release table in the README."""

WORKFLOWS = {
    ".github/templates/build.yml.j2": ".github/workflows/build.yml",
}
"""Generated workflows (template -> output), relative to the repo root."""

COMMAND = "uv run moosecontainers"
"""The command for running these utilities, used in hints."""
