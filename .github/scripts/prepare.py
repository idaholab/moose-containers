import argparse
import base64
import requests
import subprocess
import yaml
import os
import jinja2
from copy import deepcopy
from tabulate import tabulate
from typing import Optional, Tuple
import datetime

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
"""Root path to the repo."""

REPO = "idaholab/moose-containers"
"""The GitHub repository."""

URI_PREFIX = f"ghcr.io/{REPO}"
"""URI prefix for container pushes."""

CONTAINERS_FILE = "containers.yml"
"""The path to the containers.yml file, relative to the repo root."""

PACKAGES_FILE = "packages.yml"
"""The path to the packages.yml file, relative to the repo root."""

GITHUB_ACTION = os.environ.get("GITHUB_ACTIONS") == "true"
"""Whether or not we're executed in a github action."""


class ContainersException(Exception):
    def __init__(self, name: str, message: str):
        super().__init__(f"{CONTAINERS_FILE}: {name}: {message}")


def git_show(path: str, ref: str) -> str:
    """Use git to show a file at the given reference."""
    cmd = ["git", "show", f"{ref}:{path}"]
    return subprocess.check_output(cmd, cwd=REPO_ROOT, text=True)


class Container:
    """Data class for a single container to be built."""

    def __init__(self, name: str, tags: list[str], date: str, release: bool = False):
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

        self._from_container: Optional["Container"] = None
        """The container this container is built from, if any."""

        self._pr_tag: Optional[int] = None
        """Whether or not this container has a PR name/tag. Used in the URI."""

        self._main_tag: bool = False
        """Whether or not this container has a main name/tag. Used in the URI."""

        self._release_tag: bool = False
        """Whether or not this container has a release name/tag. Used in the URI."""

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
    def from_container(self) -> Optional["Container"]:
        assert self._from_container is None or isinstance(
            self._from_container, Container
        )
        return self._from_container

    @property
    def tag(self) -> str:
        """Get the tag for this container."""
        parents = []
        parent = self.from_container
        while parent is not None:
            parents.append(parent)
            parent = parent.from_container

        parent_tags = []
        for parent in parents[::-1]:
            parent_tags.extend(parent._tags)
        parent = self.from_container

        tags = parent_tags + self._tags
        tag = f"{'-'.join(tags)}-{self.raw_date}"
        if self._pr_tag is not None:
            assert not self._main_tag
            assert not self._release_tag
            tag = f"pr{self._pr_tag}-{tag}"
        return tag

    @property
    def repo(self) -> str:
        """Get the repo for this container."""
        prefix = ""
        if self._pr_tag is not None:
            assert not self._main_tag
            assert not self._release_tag
            prefix += f"pr-"
        elif self._main_tag:
            assert not self._release_tag
            prefix += "main-"
        return f"{prefix}{self.name}"

    @property
    def uri(self) -> str:
        """Get the URI for this container."""
        return f"{URI_PREFIX}/{self.repo}:{self.tag}"

    @property
    def url(self) -> str:
        """Get the URL on GitHub for this repo."""
        return (
            f"https://github.com/{REPO}/pkgs/container/moose-containers%2F{self.repo}"
        )

    def exists(self, ghcr_token: str) -> bool:
        return github_container_exists(self, ghcr_token)

    def set_from_container(self, from_container: "Container"):
        """Set the from container. Can only be called once."""
        assert isinstance(from_container, Container)
        assert self._from_container is None
        self._from_container = from_container

    def set_pr_tag(self, pr: int):
        assert isinstance(pr, int)
        assert self._pr_tag is None
        assert not self._main_tag
        assert not self._release_tag
        self._pr_tag = pr

    def set_main_tag(self):
        assert self._pr_tag is None
        assert not self._main_tag
        assert not self._release_tag
        self._main_tag = True

    def set_release_tag(self):
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
        return Container(name=name, **values)

    containers = {k: build_container(k, v) for k, v in result.items()}

    # Setup container_from
    for name, from_value in from_values.items():
        from_container = containers.get(from_value)
        if from_container is None:
            raise ContainersException(name, f"from container {from_value} not found")
        containers[name].set_from_container(from_container)

    return containers


def load_current() -> Tuple[dict[str, Container], dict]:
    """Render the current containers.yml template with the current packages.yml."""

    # Load packages config
    with open(os.path.join(REPO_ROOT, PACKAGES_FILE), "r") as f:
        packages = dict(yaml.safe_load(f))

    containers_template = jinja2.FileSystemLoader(REPO_ROOT)
    return load_containers(containers_template, packages), packages


def load_previous(ref: str) -> Tuple[dict[str, Container], dict]:
    """Render a previous containers.yaml template at the given git reference."""
    containers_template = git_show(CONTAINERS_FILE, ref)
    packages = yaml.safe_load(git_show(PACKAGES_FILE, ref))
    return load_containers(containers_template, packages), packages


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare container listing and changes."
    )

    parent = argparse.ArgumentParser(add_help=False)

    action_parser = parser.add_subparsers(dest="action", help="Action to perform")
    action_parser.required = True

    def add_common(parser: argparse.ArgumentParser, require_token: bool = False):
        parser.add_argument(
            "--github-token", type=str, help="The github token", required=require_token
        )

    def add_base_ref(parser: argparse.ArgumentParser):
        parser.add_argument(
            "base_ref", type=str, help="The base git reference to compare against."
        )

    pr_parser = action_parser.add_parser(
        "pr",
        parents=[parent],
        help="Perform the pull request action.",
    )
    pr_parser.add_argument("pr", type=int, help="The pull request number.")
    add_base_ref(pr_parser)
    add_common(pr_parser)

    push_parser = action_parser.add_parser(
        "push",
        parents=[parent],
        help="Perform the push action.",
    )
    add_base_ref(push_parser)
    add_common(push_parser)

    release_parser = action_parser.add_parser("release", parents=[parent])
    add_common(release_parser, require_token=True)

    return parser.parse_args()


def print_section(title: str, contents: str | list[str]):
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


def get_github_headers(github_token: str) -> dict:
    """Get the headers for authenticating to the GitHub API."""
    return {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def github_get_pr_comment(pr: int, marker: str, github_token: str) -> Optional[int]:
    """Find a previous comment from this job by looking for our marker."""
    url = f"https://api.github.com/repos/{REPO}/issues/{pr}/comments"

    while url:
        response = requests.get(url, headers=get_github_headers(github_token))
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
    url = f"https://api.github.com/repos/{REPO}/issues/comments/{comment_id}"
    response = requests.delete(url, headers=get_github_headers(github_token))
    response.raise_for_status()
    print(f"Deleted previous comment {comment_id}")


def github_post_pr_comment(pr: int, body: str, marker: str, github_token: str):
    """Post a new comment to the PR, deleting the old one with the same marker."""
    existing_id = github_get_pr_comment(pr, marker, github_token)

    if existing_id is not None:
        github_delete_pr_comment(existing_id, github_token)

    url = f"https://api.github.com/repos/{REPO}/issues/{pr}/comments"
    payload = {"body": f"{marker}\n{body}"}
    response = requests.post(
        url, json=payload, headers=get_github_headers(github_token)
    )
    response.raise_for_status()
    print(f"Posted comment: {response.json()['id']}")


def github_get_ghcr_token(github_token: str, name: str):
    response = requests.get(
        "https://ghcr.io/token",
        params={"service": "ghcr.io", "scope": f"repository:{REPO}/{name}:pull"},
        auth=("token", github_token),
    )
    response.raise_for_status()
    return response.json().get("token")


def github_ghcr_token(github_token: str) -> str:
    response = requests.get(
        "https://ghcr.io/token",
        params={
            "service": "ghcr.io",
            "scope": f"repository:{REPO}/moose-containers:pull",
        },
        auth=("token", github_token),
    )
    response.raise_for_status()
    return response.json()["token"]


def github_container_exists(container: Container, ghcr_token: str) -> bool:
    """Check if the given container exists on GitHub."""
    url = f"https://ghcr.io/v2/{REPO}/{container.repo}/manifests/{container.tag}"
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


def run_with_base(
    base_ref: str,
    pr: Optional[int] = None,
    main: bool = False,
    github_token: Optional[str] = None,
) -> str:
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
        tag = container.tag
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
            unreleased_summary.append((f"`{name}`", f"`{release_container.uri}`"))

        if base_container is not None and base_container.date > container.date:
            raise ContainersException(name, "date moved back")

        build = base_container is None or tag != base_container.tag
        if build and pr is not None:
            container.set_pr_tag(pr)
        else:
            container.set_main_tag()

        if not build and ghcr_token and main and not container.exists(ghcr_token):
            print(f"::warning::Container {container.uri} does not exist; building")
            build = True

        if build:
            if base_container is not None and base_container.date > container.date:
                raise ContainersException(name, "date moved back")
            changed[name] = True
            summary_name = f"[`{name}`]({container.url})"
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
            base_value_output = f"`{base_value}`" if base_value is not None else "ADDED"
            package_summary.append((f"`{name}`", base_value_output, value_output))

    # Build summary table
    build_output = "## Container builds\n\n"
    if build_summary:
        build_output += tabulate(
            build_summary, headers=["container", "base tag", "uri"], tablefmt="github"
        )
    else:
        build_output += "No containers to build"
    if GITHUB_ACTION:
        build_output += "\n\n"
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(build_output)
    print_section("Container build summary", build_output)

    # Packages summary table
    packages_output = "## Packages changed\n\n"
    if package_summary:
        packages_output += tabulate(
            package_summary,
            headers=["package", "base value", "value"],
            tablefmt="github",
        )
    else:
        packages_output += "No packages changed"
    if GITHUB_ACTION:
        packages_output += "\n\n"
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(packages_output)
    print_section("Packages changed summary", packages_output)

    # Unreleased table
    unreleased_output = "## Unreleased containers\n\n"
    if unreleased_summary:
        unreleased_output += tabulate(
            unreleased_summary, headers=["container", "url"], tablefmt="github"
        )
    else:
        unreleased_output += "No unreleased containers"
    if GITHUB_ACTION:
        unreleased_output += "\n\n"
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(unreleased_output)
    print_section("Unreleased containers summary", unreleased_output)

    # Do github output
    result = {f"uri-{k}": v for k, v in uris.items()}
    result.update({f"changed-{k}": "1" if v else "" for k, v in changed.items()})
    result.update({f"package-{k}": v for k, v in packages.items()})
    output = []
    for k, v in result.items():
        value = f"{k}={v}"
        output.append(value)
        if GITHUB_ACTION:
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"{value}\n")
    print_section("Output", output)

    return build_output + packages_output + unreleased_output


def action_pr(args: argparse.Namespace):
    pr = args.pr
    github_token = args.github_token

    result = run_with_base(args.base_ref, pr, github_token=github_token)

    # Pull request comment
    if GITHUB_ACTION and github_token:
        print("::group::Post pull request comment")
        marker = "<!-- prepare summary -->"
        github_post_pr_comment(pr, result, marker, github_token)
        print("::endgroup::")


def action_push(args: argparse.Namespace):
    run_with_base(args.base_ref, main=True, github_token=args.github_token)


def action_release(args: argparse.Namespace):
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
            print(f"::error Main container {main_container.uri} does not exist")
            missing_containers = True

        release_from[name] = main_container.uri
        release_to[name] = container.uri
        release_summary.append(
            (
                f"[`{name}`]({container.url})",
                f"`{main_container.uri}`",
                f"`{container.uri}`",
            )
        )

    if missing_containers:
        pass

    # Build summary table
    build_output = "## Container releases\n\n"
    if release_summary:
        build_output += tabulate(
            release_summary,
            headers=["container", "main uri", "release uri"],
            tablefmt="github",
        )
    else:
        build_output += "No containers to release"
    if GITHUB_ACTION:
        build_output += "\n\n"
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(build_output)
    print_section("Container release summary", build_output)

    # Do github output
    result = {f"from-{k}": v for k, v in release_from.items()}
    result.update({f"to-{k}": v for k, v in release_to.items()})
    output = []
    for k, v in result.items():
        value = f"{k}={v}"
        output.append(value)
        if GITHUB_ACTION:
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"{value}\n")
    print_section("Output", output)


def main():
    args = parse_args()

    if args.action == "pr":
        action_pr(args)
    elif args.action == "push":
        action_push(args)
    elif args.action == "release":
        action_release(args)


if __name__ == "__main__":
    main()
