"""CI utilities for building, releasing, and cleaning MOOSE containers."""

import argparse
import datetime
import os
import re
import subprocess
import sys
import urllib.parse
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass

import jinja2
import requests
import yaml
from tabulate import tabulate

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
"""Root path to the repo."""

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

GITHUB_ACTION = os.environ.get("GITHUB_ACTIONS") == "true"
"""Whether or not we're executed in a github action."""

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


class ContainersException(Exception):
    """Exception for an error in the containers file."""

    def __init__(self, name: str, message: str):
        """Initialize the exception for the given container name."""
        super().__init__(f"{CONTAINERS_FILE}: {name}: {message}")


def git_show(path: str, ref: str) -> str:
    """Use git to show a file at the given reference."""
    cmd = ["git", "show", f"{ref}:{path}"]
    return subprocess.check_output(cmd, cwd=REPO_ROOT, text=True)


class Container:
    """Data class for a single container to be built."""

    def __init__(
        self, name: str, tags: list[str], date: str, release: bool = False
    ):
        """Initialize the container."""
        assert isinstance(name, str)
        assert isinstance(tags, list)
        assert all(isinstance(v, str) for v in tags)
        assert isinstance(date, str)
        assert isinstance(release, bool)

        self._name: str = name
        """Name of the container."""

        self._tags: list[str] = tags
        """Tags for the container."""

        try:
            date_parsed = datetime.datetime.strptime(date, "%Y%m%d").date()
        except Exception as e:
            raise ContainersException(name, f"date='{date}' is invalid") from e
        if date_parsed > datetime.date.today():
            raise ContainersException(name, f"date='{date}' is from the future")

        self._date: datetime.date = date_parsed
        """The date for this container."""

        self._raw_date: str = date
        """The raw string date for this container."""

        self._release: bool = release
        """Whether or not this container should be released."""

        self._from_container: Container | None = None
        """The container this container is built from, if any."""

        self._pr_tag: int | None = None
        """Whether or not this container has a PR name/tag. Used in the URI."""

        self._main_tag: bool = False
        """Whether or not this container has a main name/tag (for the URI)."""

        self._release_tag: bool = False
        """Whether or not this container has a release tag (for the URI)."""

    @property
    def name(self) -> str:
        """The name of the container."""
        return self._name

    @property
    def date(self) -> datetime.date:
        """The date for the container."""
        return self._date

    @property
    def raw_date(self) -> str:
        """The raw (string) date for this container."""
        return self._raw_date

    @property
    def release(self) -> bool:
        """Whether or not this container should be released."""
        return self._release

    @property
    def from_container(self) -> Container | None:
        """The container this container is built from, if any."""
        assert self._from_container is None or isinstance(
            self._from_container, Container
        )
        return self._from_container

    @staticmethod
    def get_pr_tag_prefix(pr_num: int) -> str:
        """Get the tag prefix for a pull request container."""
        return f"pr{pr_num}-"

    @staticmethod
    def get_main_tag_prefix() -> str:
        """Get the tag prefix for a main event container."""
        return "main-"

    @property
    def raw_tag(self) -> str:
        """Get the raw (without any prefixes) tag for this container."""
        parents = []
        parent = self.from_container
        while parent is not None:
            parents.append(parent)
            parent = parent.from_container

        parent_tags = []
        for parent in parents[::-1]:
            parent_tags.extend(parent._tags)
        parent = self.from_container

        return "-".join(parent_tags + self._tags + [self.raw_date])

    @property
    def tag(self) -> str:
        """Get the tag for this container."""
        tag = self.raw_tag
        if self._pr_tag is not None:
            assert not self._main_tag
            assert not self._release_tag
            tag = f"{self.get_pr_tag_prefix(self._pr_tag)}{tag}"
        elif self._main_tag:
            assert not self._release_tag
            tag = f"{self.get_main_tag_prefix()}{tag}"
        return tag

    @property
    def repo(self) -> str:
        """Get the repo for this container."""
        prefix = ""
        if self._pr_tag is not None:
            assert not self._main_tag
            assert not self._release_tag
            prefix += STAGING_PREFIX
        elif self._main_tag:
            assert not self._release_tag
            prefix += STAGING_PREFIX
        return f"{prefix}{self.name}"

    @property
    def uri(self) -> str:
        """Get the URI for this container."""
        return f"{URI_PREFIX}/{self.repo}:{self.tag}"

    @property
    def url(self) -> str:
        """Get the URL on GitHub for this repo."""
        return f"https://github.com/{FULL_REPO}/pkgs/container/moose-containers%2F{self.repo}"

    def exists(self, ghcr_token: str) -> bool:
        """Check if this container exists in the registry."""
        return github_container_exists(self, ghcr_token)

    def set_from_container(self, from_container: Container):
        """Set the from container. Can only be called once."""
        assert isinstance(from_container, Container)
        assert self._from_container is None
        self._from_container = from_container

    def set_pr_tag(self, pr: int):
        """Set the pull request tag. Can only be called once."""
        assert isinstance(pr, int)
        assert self._pr_tag is None
        assert not self._main_tag
        assert not self._release_tag
        self._pr_tag = pr

    def set_main_tag(self):
        """Set the main tag. Can only be called once."""
        assert self._pr_tag is None
        assert not self._main_tag
        assert not self._release_tag
        self._main_tag = True

    def set_release_tag(self):
        """Set the release tag. Can only be called once."""
        assert self._pr_tag is None
        assert not self._main_tag
        assert not self._release_tag
        self._release_tag = True


def load_containers(
    template: jinja2.FileSystemLoader | dict, packages: dict
) -> dict[str, Container]:
    """Render a containers.yml template with the given packages input."""
    if isinstance(template, jinja2.FileSystemLoader):
        env = jinja2.Environment(loader=template)
        template = env.get_template(CONTAINERS_FILE)
    else:
        template = jinja2.Template(template)

    # Helper for package("") function in jninja
    def get_package(name: str):
        value = packages.get(name)
        if value is None:
            raise KeyError(f"Unknown package {name} in packages.yml")
        return value

    # Render containers.yml
    output = template.render(package=get_package)
    result = yaml.safe_load(output)

    # Build Container objects without container_from
    from_values = {}

    def build_container(name: str, values: dict):
        if container_from := values.get("from"):
            from_values[name] = container_from
            del values["from"]
        return Container(name=f"moose-{name}", **values)

    containers = {k: build_container(k, v) for k, v in result.items()}

    # Setup container_from
    for name, from_value in from_values.items():
        from_container = containers.get(from_value)
        if from_container is None:
            raise ContainersException(
                name, f"from container {from_value} not found"
            )
        containers[name].set_from_container(from_container)

    return containers


def load_current() -> tuple[dict[str, Container], dict]:
    """Render the current containers.yml with the current packages.yml."""
    # Load packages config
    with open(os.path.join(REPO_ROOT, PACKAGES_FILE), "r") as f:
        packages = dict(yaml.safe_load(f))

    containers_template = jinja2.FileSystemLoader(REPO_ROOT)
    return load_containers(containers_template, packages), packages


def load_previous(ref: str) -> tuple[dict[str, Container], dict]:
    """Render a previous containers.yaml template at the given git reference."""
    containers_template = git_show(CONTAINERS_FILE, ref)
    packages = yaml.safe_load(git_show(PACKAGES_FILE, ref))
    return load_containers(containers_template, packages), packages


def parse_args():
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(
        description="Prepare container listing and changes."
    )

    parent = argparse.ArgumentParser(add_help=False)

    action_parser = parser.add_subparsers(
        dest="action", help="Action to perform"
    )
    action_parser.required = True

    def add_common(
        parser: argparse.ArgumentParser,
        require_token: bool = False,
        dry_run: bool = False,
    ):
        parser.add_argument(
            "--github-token",
            type=str,
            help="The github token",
            required=require_token,
        )
        if dry_run:
            parser.add_argument(
                "--dry-run", action="store_true", help="Preform a dry run."
            )

    def add_base_ref(parser: argparse.ArgumentParser):
        parser.add_argument(
            "base_ref",
            type=str,
            help="The base git reference to compare against.",
        )

    def add_pr(parser: argparse.ArgumentParser):
        parser.add_argument("pr", type=int, help="The pull request number.")

    # prepare_pr action
    prepare_pr_parser = action_parser.add_parser(
        "prepare_pr",
        parents=[parent],
        help="Perform the pull request action.",
    )
    add_pr(prepare_pr_parser)
    add_base_ref(prepare_pr_parser)
    add_common(prepare_pr_parser)

    # prepare_push action
    prepare_push_action = action_parser.add_parser(
        "prepare_push",
        parents=[parent],
        help="Perform the push action.",
    )
    add_base_ref(prepare_push_action)
    add_common(prepare_push_action)

    # prepare_release action
    prepare_release_parser = action_parser.add_parser(
        "prepare_release", parents=[parent]
    )
    add_common(prepare_release_parser, require_token=True)

    # post_pr action
    post_pr_parser = action_parser.add_parser(
        "post_pr",
        parents=[parent],
        help=(
            "Perform the post-pull request action (check if containers exist)."
        ),
    )
    add_pr(post_pr_parser)
    add_common(post_pr_parser)

    # post_push action
    post_push_parser = action_parser.add_parser(
        "post_push",
        parents=[parent],
        help="Perform the post-push action (check if containers exist).",
    )
    add_common(post_push_parser)

    # post_release action
    post_release_parser = action_parser.add_parser(
        "post_release",
        parents=[parent],
        help=(
            "Perform the post-release request action "
            "(check if containers exist)."
        ),
    )
    add_common(post_release_parser)

    # delete_untagged action
    delete_untagged_parser = action_parser.add_parser(
        "delete_untagged",
        parents=[parent],
        help="Delete untagged images.",
    )
    add_common(delete_untagged_parser, require_token=True, dry_run=True)

    # delete_pr action
    delete_pr_parser = action_parser.add_parser(
        "delete_pr",
        parents=[parent],
        help="Delete pull request images.",
    )
    add_common(delete_pr_parser, require_token=True, dry_run=True)
    add_pr(delete_pr_parser)
    delete_pr_parser.add_argument(
        "--only-cache",
        action="store_true",
        help="Only delete the cache, not the final images.",
    )
    delete_pr_parser.add_argument(
        "--only-images",
        action="store_true",
        help="Only delete the final images, not the cache.",
    )
    delete_pr_parser.add_argument(
        "--allow-missing-repos",
        action="store_true",
        help="Allow repositories to not exist.",
    )

    # delete_all_prs action
    delete_all_prs_parser = action_parser.add_parser(
        "delete_all_prs",
        parents=[parent],
        help="Delete all pull request images.",
    )
    add_common(delete_all_prs_parser, require_token=True, dry_run=True)

    # readme action
    readme_parser = action_parser.add_parser(
        "readme",
        parents=[parent],
        help=f"Update the release table in {README_FILE}.",
    )
    readme_parser.add_argument(
        "--check",
        action="store_true",
        help="Only check that the table is up to date.",
    )

    return parser.parse_args()


def print_section(title: str, contents: str | list[str]):
    """Print a section of output, grouped when in a GitHub action."""
    github = os.environ.get("GITHUB_ACTIONS") == "true"

    if github:
        print(f"::group::{title}")
    else:
        print(f"-- {title}\n")

    if isinstance(contents, str):
        print(contents)
    else:
        print("\n".join(contents))

    if github:
        print("::endgroup::")
    else:
        print()


def build_summary_table(
    title: str, rows: list[tuple], headers: list[str], empty: str
) -> str:
    """Build a markdown summary section with a table, or a note if empty.

    Also prints it and, in a GitHub action, appends it to the step summary.
    """
    output = f"## {title}\n\n"
    if rows:
        output += tabulate(rows, headers=headers, tablefmt="github")
    else:
        output += empty
    if GITHUB_ACTION:
        output += "\n\n"
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(output)
    print_section(f"{title} summary", output)
    return output


def write_outputs(outputs: dict[str, str]):
    """Print the given step outputs and write them in a GitHub action."""
    lines = [f"{k}={v}" for k, v in outputs.items()]
    if GITHUB_ACTION:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.writelines(f"{line}\n" for line in lines)
    print_section("Output", lines)


def get_github_api_headers(github_token: str) -> dict:
    """Get the headers for authenticating to the GitHub API."""
    return {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def github_api_delete(url: str, token: str):
    """Call DELETE on the GitHub API."""
    response = requests.delete(
        f"{GITHUB_API_URL}{url}", headers=get_github_api_headers(token)
    )
    response.raise_for_status()


def github_get_pr_comment(
    pr: int, marker: str, github_token: str
) -> int | None:
    """Find a previous comment from this job by looking for our marker."""
    url = f"{GITHUB_API_URL}repos/{FULL_REPO}/issues/{pr}/comments"

    while url:
        response = requests.get(
            url, headers=get_github_api_headers(github_token)
        )
        response.raise_for_status()
        comments = response.json()

        for comment in comments:
            if marker in comment["body"]:
                id = comment["id"]
                assert isinstance(id, int)
                return id

        # Handle pagination
        url = response.links.get("next", {}).get("url")

    return None


def github_delete_pr_comment(comment_id: int, github_token: str):
    """Delete a GitHub comment by ID."""
    github_api_delete(
        f"repos/{FULL_REPO}/issues/comments/{comment_id}", github_token
    )
    print(f"Deleted previous comment {comment_id}")


def github_post_pr_comment(pr: int, body: str, marker: str, github_token: str):
    """Post a new comment to the PR, deleting the old one with the marker."""
    existing_id = github_get_pr_comment(pr, marker, github_token)

    if existing_id is not None:
        github_delete_pr_comment(existing_id, github_token)

    url = f"{GITHUB_API_URL}repos/{FULL_REPO}/issues/{pr}/comments"
    payload = {"body": f"{marker}\n{body}"}
    response = requests.post(
        url, json=payload, headers=get_github_api_headers(github_token)
    )
    response.raise_for_status()
    print(f"Posted comment: {response.json()['id']}")


def github_ghcr_token(github_token: str) -> str:
    """Get a GitHub GHCR token."""
    response = requests.get(
        "https://ghcr.io/token",
        params={
            "service": "ghcr.io",
            "scope": f"repository:{FULL_REPO}/moose-containers:pull",
        },
        auth=("token", github_token),
    )
    response.raise_for_status()
    return response.json()["token"]


def github_container_exists(container: Container, ghcr_token: str) -> bool:
    """Check if the given container exists on GitHub."""
    url = f"https://ghcr.io/v2/{FULL_REPO}/{container.repo}/manifests/{container.tag}"
    headers = {
        "Authorization": f"Bearer {ghcr_token}",
        "Accept": "application/vnd.oci.image.index.v1+json",
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return True
    if (
        response.status_code == 404
        and (errors := response.json().get("errors")) is not None
        and len(errors) == 1
        and errors[0].get("code") == "MANIFEST_UNKNOWN"
    ):
        return False
    response.raise_for_status()
    return False


def github_api_get_paginated(url: str, token: str) -> list[dict]:
    """Call GET on the GitHub API with pagination."""
    url = f"{GITHUB_API_URL}{url}"
    result: list[dict] = []
    headers = get_github_api_headers(token)
    params: dict | None = {"per_page": 100}
    while url:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        result.extend(response.json())

        url = response.links.get("next", {}).get("url")
        params = None

    return result


@dataclass
class GitHubContainer:
    """Data storge for a single container on GitHub."""

    name: str
    """Full name of the container."""
    id: int
    """GitHub ID for the container."""
    tags: list[str]
    """Tags for the container."""
    sha: str
    """The SHA for the container."""
    uri: str
    """URI for the container (sha256 definition, no tags)."""


class GitHubContainerRepoMissing(Exception):
    """Exception raised when a container repository is missing."""


def github_get_containers(repo: str, token: str) -> list[GitHubContainer]:
    """Get all of the containers under the given container repo."""
    name = f"{REPO}/{repo}"

    quoted_name = urllib.parse.quote(name, safe="")
    url = f"orgs/{ORG}/packages/container/{quoted_name}/versions"
    try:
        result = github_api_get_paginated(url, token)
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise GitHubContainerRepoMissing from e
        else:
            raise

    return [
        GitHubContainer(
            name=name,
            id=v["id"],
            tags=v["metadata"]["container"]["tags"],
            sha=v["name"].split(":")[-1],
            uri=f"{URI_PREFIX}/{repo}@{v['name']}",
        )
        for v in result
    ]


def github_delete_container(github_container: GitHubContainer, token: str):
    """Delete a container from the GitHub container repository."""
    quoted_name = urllib.parse.quote(github_container.name, safe="")
    url = f"orgs/{ORG}/packages/container/{quoted_name}/versions"
    github_api_delete(f"{url}/{github_container.id}", token)


def prepare_with_base(
    base_ref: str,
    pr: int | None = None,
    main: bool = False,
    github_token: str | None = None,
) -> str:
    """Prepare a build by comparing against the given base reference."""
    assert pr is not None or main
    assert (pr is not None) != main

    current_containers, packages = load_current()
    base_containers, base_packages = load_previous(base_ref)

    # Set main state for base containers
    [container.set_main_tag() for container in base_containers.values()]

    # Get a ghcr token for determining packing existance
    ghcr_token = None
    if github_token:
        ghcr_token = github_ghcr_token(github_token)

    # Determine changed containers
    uris = {}
    changed = {}
    build_summary = []
    unreleased_summary = []
    for name in sorted(current_containers):
        container = current_containers[name]
        base_container = base_containers.get(name)

        # Release version of the container, for checking status
        release_container = None
        if container.release:
            release_container = deepcopy(container)
            release_container.set_release_tag()

        # Keep track of unreleased containers
        if (
            release_container is not None
            and ghcr_token
            and not release_container.exists(ghcr_token)
        ):
            unreleased_summary.append(
                (f"`{container.name}`", f"`{release_container.uri}`")
            )

        if base_container is not None and base_container.date > container.date:
            raise ContainersException(container.name, "date moved back")

        build = (
            base_container is None
            or container.raw_tag != base_container.raw_tag
        )

        if build and pr is not None:
            container.set_pr_tag(pr)
        else:
            container.set_main_tag()

        if (
            not build
            and ghcr_token
            and main
            and not container.exists(ghcr_token)
        ):
            print(
                f"::warning::Container {container.uri} does not exist; building"
            )
            build = True

        if build:
            changed[name] = True
            summary_name = f"[`{container.name}`]({container.url})"
            build_summary.append(
                (
                    summary_name,
                    f"`{base_container.tag}`" if base_container else "",
                    f"`{container.uri}`",
                )
            )
        else:
            changed[name] = False

        uris[name] = container.uri

    # Determine changed packages
    package_summary = []
    for name in sorted(packages.keys() | base_packages.keys()):
        value = packages.get(name)
        base_value = base_packages.get(name)
        if value != base_value:
            value_output = f"`{value}`" if value is not None else "REMOVED"
            base_value_output = (
                f"`{base_value}`" if base_value is not None else "ADDED"
            )
            package_summary.append(
                (f"`{name}`", base_value_output, value_output)
            )

    # Summary tables
    build_output = build_summary_table(
        "Container builds",
        build_summary,
        ["container", "base tag", "uri"],
        "No containers to build",
    )
    packages_output = build_summary_table(
        "Packages changed",
        package_summary,
        ["package", "base value", "value"],
        "No packages changed",
    )
    unreleased_output = build_summary_table(
        "Unreleased containers",
        unreleased_summary,
        ["container", "url"],
        "No unreleased containers",
    )

    # Do github output
    result = {f"uri-{k}": v for k, v in uris.items()}
    result.update(
        {f"changed-{k}": "1" if v else "" for k, v in changed.items()}
    )
    result.update({f"package-{k}": v for k, v in packages.items()})
    write_outputs(result)

    return build_output + packages_output + unreleased_output


def action_prepare_pr(args: argparse.Namespace):
    """Perform the prepare_pr action."""
    pr = args.pr
    github_token = args.github_token

    result = prepare_with_base(args.base_ref, pr, github_token=github_token)

    # Pull request comment
    if GITHUB_ACTION and github_token:
        print("::group::Post pull request comment")
        marker = "<!-- prepare summary -->"
        github_post_pr_comment(pr, result, marker, github_token)
        print("::endgroup::")


def action_prepare_push(args: argparse.Namespace):
    """Perform the prepare_push action."""
    prepare_with_base(args.base_ref, main=True, github_token=args.github_token)


def action_prepare_release(args: argparse.Namespace):
    """Perform the prepare_release action."""
    github_token = args.github_token

    containers, _ = load_current()

    # Get a ghcr token for determining packing existance
    ghcr_token = github_ghcr_token(github_token)

    # Whether or not we're missing containers for a release
    missing_containers = False

    release_from = {}
    release_to = {}
    release_summary = []
    for name in sorted(containers):
        container = containers[name]

        # Shouldn't be released
        if not container.release:
            continue

        # Setup container URIs
        main_container = deepcopy(container)
        main_container.set_main_tag()
        container.set_release_tag()

        release_from[name] = main_container.uri

        # Skip containers already released
        if container.exists(ghcr_token):
            release_to[name] = ""
            continue

        # Check for existance of main container
        if not main_container.exists(ghcr_token):
            print(
                f"::error::Main container {main_container.uri} does not exist"
            )
            missing_containers = True

        release_to[name] = container.uri
        release_summary.append(
            (
                f"[`{name}`]({container.url})",
                f"`{main_container.uri}`",
                f"`{container.uri}`",
            )
        )

    if missing_containers:
        sys.exit(1)

    # Summary table
    build_summary_table(
        "Container releases",
        release_summary,
        ["container", "main uri", "release uri"],
        "No containers to release",
    )

    # Do github output
    result = {f"from-{k}": v for k, v in release_from.items()}
    result.update({f"to-{k}": v for k, v in release_to.items()})
    write_outputs(result)


def post_action(
    github_token: str, pr: int | None = None, release: bool = False
):
    """Check that the expected containers exist after a build."""
    ghcr_token = github_ghcr_token(github_token)

    containers, _ = load_current()

    main_containers = deepcopy(containers)
    [v.set_main_tag() for v in main_containers.values()]

    pr_containers = {}
    if pr is not None:
        pr_containers = deepcopy(containers)
        [v.set_pr_tag(pr) for v in pr_containers.values()]

    release_containers = {}
    if release:
        release_containers = deepcopy(containers)
        [v.set_release_tag() for v in release_containers.values()]

    def check_exists(name: str, containers: dict[str, Container]) -> bool:
        other_container = containers.get(name)
        if other_container is None:
            return False
        print(f"  {other_container.uri}... ", end="")
        if other_container.exists(ghcr_token):
            print("exists")
            return True
        print("does not exist")
        return False

    missing_containers: list[str] = []
    for name, container in containers.items():
        if release and not container.release:
            continue

        print(f"Checking {container.name}:{container.tag}...")

        if release:
            if check_exists(name, release_containers):
                continue
        else:
            if pr is not None and check_exists(name, pr_containers):
                continue
            if check_exists(name, main_containers):
                continue

        missing_containers.append(f"{container.name}:{container.tag}")

    if missing_containers:
        print(
            "\nThe following container(s) do not exist in the container "
            "registry:\n\n  - " + "\n  - ".join(missing_containers)
        )
        sys.exit(1)


def action_post_pr(args: argparse.Namespace):
    """Perform the post_pr action."""
    post_action(args.github_token, pr=args.pr)


def action_post_push(args: argparse.Namespace):
    """Perform the post_push action."""
    post_action(args.github_token)


def action_post_release(args: argparse.Namespace):
    """Perform the post_release action."""
    post_action(args.github_token, release=True)


def delete_containers(
    condition: Callable[[GitHubContainer], bool],
    token: str,
    dry_run: bool,
    allow_missing_repos: bool,
):
    """Delete staging containers that match the given condition."""
    current_containers, _ = load_current()

    missing_repos = []
    num_deleted = 0
    for container in current_containers.values():
        name = f"{STAGING_PREFIX}{container.repo}"
        print(f"Checking {name}...")

        try:
            github_containers = github_get_containers(name, token)
        except GitHubContainerRepoMissing:
            missing_repos.append(name)
            print(f"  {container.repo} does not exist")
            continue

        for github_container in github_containers:
            if "latest" in github_container.tags:
                continue

            assert len(github_container.tags) < 2, "Should one or no tags"

            if condition(github_container):
                if len(github_container.tags) == 1:
                    context = github_container.uri.replace(
                        "@", f":{github_container.tags[0]}@"
                    )
                else:
                    context = github_container.uri
                context += f" id={github_container.id}"
                if dry_run:
                    print(f"  Would delete {context}")
                else:
                    print(f"  Deleting {context}...")
                    github_delete_container(github_container, token)
                    num_deleted += 1

    print(f"\nDeleted {num_deleted} image(s)")

    if missing_repos:
        print(
            "\nThe following container repo(s) do not exist:\n\n"
            + "\n".join(missing_repos)
        )
        if not allow_missing_repos:
            sys.exit(1)


def action_delete_untagged(args: argparse.Namespace):
    """Perform the delete_untagged action."""

    def condition(github_container: GitHubContainer) -> bool:
        return len(github_container.tags) == 0

    delete_containers(condition, args.github_token, args.dry_run, False)


def action_delete_pr(args: argparse.Namespace):
    """Perform the delete_pr action."""
    pr = args.pr
    only_cache = args.only_cache
    only_images = args.only_images

    if only_cache and only_images:
        print("ERROR: Cannot supply --only-cache and --only-images")
        sys.exit(1)

    prefix = Container.get_pr_tag_prefix(pr)
    cache_tag = f"{prefix}cache"

    def condition(github_container: GitHubContainer) -> bool:
        if len(github_container.tags) == 0:
            return False
        tag = github_container.tags[0]

        if only_cache:
            return tag == cache_tag
        if only_images:
            return tag != cache_tag and tag.startswith(prefix)
        return tag.startswith(prefix)

    delete_containers(
        condition, args.github_token, args.dry_run, args.allow_missing_repos
    )


def action_delete_all_prs(args: argparse.Namespace):
    """Perform the delete_all_prs action."""

    def condition(github_container: GitHubContainer) -> bool:
        return (
            len(github_container.tags) == 1
            and re.match("^pr[0-9]+-", github_container.tags[0]) is not None
        )

    delete_containers(condition, args.github_token, args.dry_run, False)


def build_readme_releases() -> str:
    """Build the markdown table of release containers for the README."""
    containers, _ = load_current()

    rows = []
    for name in sorted(containers):
        container = containers[name]
        if not container.release:
            continue
        container.set_release_tag()
        rows.append(
            (
                f"[`{container.name}`]({container.url})",
                f"`{container.tag}`",
            )
        )

    return tabulate(rows, headers=["container", "tag"], tablefmt="github")


def action_readme(args: argparse.Namespace):
    """Perform the readme action."""
    path = os.path.join(REPO_ROOT, README_FILE)
    with open(path, "r") as f:
        contents = f.read()

    pattern = re.compile(
        f"{re.escape(README_START)}.*?{re.escape(README_END)}", re.DOTALL
    )
    if pattern.search(contents) is None:
        print(f"ERROR: {README_FILE} is missing {README_START} / {README_END}")
        sys.exit(1)

    block = f"{README_START}\n{build_readme_releases()}\n{README_END}"
    updated = pattern.sub(lambda _: block, contents)

    if updated == contents:
        print(f"{README_FILE} is up to date")
        return

    if args.check:
        print(
            f"ERROR: {README_FILE} release table is out of date; run:\n\n"
            "  uv run python .github/scripts/ci.py readme"
        )
        sys.exit(1)

    with open(path, "w") as f:
        f.write(updated)
    print(f"Updated {README_FILE}")


def main():
    """Run the action given on the command line."""
    args = parse_args()

    globals()[f"action_{args.action}"](args)


if __name__ == "__main__":
    main()
