"""Shared fixtures for the tests."""

import json
import os
import re
import subprocess

import pytest
import responses

from moosecontainers import config

PACKAGES = {"os": "1.0", "gcc": "2.0", "mpich": "3.0"}
"""The packages in the test repo."""

CONTAINERS = """\
base-os:
  dockerfile: os
  build-args:
    OS_VERSION: "{{ package("os") }}"
  tags:
    - "{{ package("os") }}"
  date: "20250101"
  release: true
compiler-os-gcc:
  from: base-os
  dockerfile: gcc
  build-args:
    GCC_VERSION: "{{ package("gcc") }}"
  tags:
    - "gcc{{ package("gcc") }}"
  date: "20250101"
mpi-os-gcc:
  from: compiler-os-gcc
  dockerfile: mpi
  tags:
    - "mpich{{ package("mpich") }}"
  date: "20250101"
  release: true
"""
"""The containers.yml in the test repo."""

README = """\
# test

<!-- releases:start -->
old
<!-- releases:end -->
"""
"""The README.md in the test repo."""

TEMPLATE = """\
[% for name, parent in containers %]
[[ name ]]: [[ parent ]]
[% endfor %]
leaves: [[ leaves | join(",") ]]
"""
"""The workflow template in the test repo."""

DOCKERFILES = ["base/os", "compiler/gcc", "mpi/mpi"]
"""The Dockerfile directories (under docker/) in the test repo."""


@pytest.fixture(autouse=True)
def no_github_action(monkeypatch):
    """Run as if not in a GitHub action, even when the tests are."""
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    monkeypatch.delenv("GITHUB_OUTPUT", raising=False)
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)


@pytest.fixture
def github_action(monkeypatch, tmp_path):
    """Run as if in a GitHub action, with temporary output files.

    Returns the paths to the (output, step summary) files.
    """
    output = tmp_path / "github_output"
    summary = tmp_path / "github_step_summary"
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    return output, summary


@pytest.fixture(autouse=True)
def mock_requests():
    """Mock all HTTP requests; any request that isn't registered fails."""
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        yield rsps


class Repo:
    """A test repo in git, used as the repo root."""

    def __init__(self, root: str):
        """Create the repo at the given root and make an initial commit."""
        self.root: str = root
        """The path to the repo."""

        self.write(config.CONTAINERS_FILE, CONTAINERS)
        self.write_packages(PACKAGES)
        self.write(config.README_FILE, README)
        for template in config.WORKFLOWS:
            self.write(template, TEMPLATE)
        for dockerfile in DOCKERFILES:
            self.write(f"docker/{dockerfile}/Dockerfile", "")

        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "test@example.com")
        self.git("config", "user.name", "test")
        self.git("config", "commit.gpgsign", "false")
        self.commit()

    def path(self, path: str) -> str:
        """Get the full path to a file in the repo."""
        return os.path.join(self.root, path)

    def read(self, path: str) -> str:
        """Read a file in the repo."""
        with open(self.path(path)) as f:
            return f.read()

    def write(self, path: str, contents: str):
        """Write a file in the repo, creating its directory."""
        full_path = self.path(path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(contents)

    def write_packages(self, packages: dict):
        """Write packages.yml in the repo."""
        contents = "".join(f'{k}: "{v}"\n' for k, v in packages.items())
        self.write(config.PACKAGES_FILE, contents)

    def write_containers(self, contents: str):
        """Write containers.yml in the repo."""
        self.write(config.CONTAINERS_FILE, contents)

    def git(self, *args: str) -> str:
        """Run git in the repo."""
        return subprocess.run(
            ["git", *args],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout

    def commit(self) -> str:
        """Commit everything in the repo, returning the commit SHA."""
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "commit")
        return self.git("rev-parse", "HEAD").strip()


@pytest.fixture
def repo(monkeypatch, tmp_path) -> Repo:
    """Create a test repo (committed in git) and use it as the repo root."""
    repo = Repo(str(tmp_path / "repo"))
    monkeypatch.setattr(config, "REPO_ROOT", repo.root)
    return repo


class Registry:
    """A mocked container registry and GitHub packages API."""

    GHCR_TOKEN = "ghcr-token"
    """The token returned when requesting a GHCR token."""

    def __init__(self, rsps: responses.RequestsMock):
        """Register the mocked endpoints."""
        self.images: set[tuple[str, str]] = set()
        """The (repo, tag) images that exist in the registry."""

        self.versions: dict[str, list[dict]] = {}
        """The package versions (by container repo) in the packages API."""

        self.deleted: list[tuple[str, int]] = []
        """The (container repo, id) package versions that were deleted."""

        rsps.get("https://ghcr.io/token", json={"token": self.GHCR_TOKEN})
        rsps.add_callback(
            responses.GET,
            re.compile(
                f"https://ghcr.io/v2/{config.FULL_REPO}/(.+)/manifests/(.+)"
            ),
            callback=self._manifest,
        )
        versions = re.compile(
            f"{config.GITHUB_API_URL}orgs/{config.ORG}/packages/container/"
            f"{config.REPO}%2F([^/?]+)/versions(?:/([0-9]+))?"
        )
        rsps.add_callback(responses.GET, versions, callback=self._versions)
        rsps.add_callback(responses.DELETE, versions, callback=self._delete)

    def add(self, uri: str):
        """Add the image with the given URI to the registry."""
        repo, tag = uri.removeprefix(f"{config.URI_PREFIX}/").split(":")
        self.images.add((repo, tag))

    def add_version(self, repo: str, id: int, tags: list[str]):
        """Add a package version to the given container repo."""
        self.versions.setdefault(repo, []).append(
            {
                "id": id,
                "name": f"sha256:{id:064x}",
                "metadata": {"container": {"tags": tags}},
            }
        )

    def _manifest(self, request):
        match = re.search("/v2/[^/]+/[^/]+/(.+)/manifests/(.+)", request.url)
        if (match.group(1), match.group(2)) in self.images:
            return (200, {}, "{}")
        body = {"errors": [{"code": "MANIFEST_UNKNOWN"}]}
        return (404, {}, json.dumps(body))

    def _versions(self, request):
        repo = re.search("%2F([^/?]+)/versions", request.url).group(1)
        if repo not in self.versions:
            return (404, {}, "{}")
        return (200, {}, json.dumps(self.versions[repo]))

    def _delete(self, request):
        match = re.search("%2F([^/?]+)/versions/([0-9]+)", request.url)
        self.deleted.append((match.group(1), int(match.group(2))))
        return (204, {}, "")


@pytest.fixture
def registry(mock_requests) -> Registry:
    """Mock the container registry and GitHub packages API."""
    return Registry(mock_requests)
