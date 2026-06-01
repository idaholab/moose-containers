import argparse
import requests
import subprocess
import yaml
import os
import jinja2
from tabulate import tabulate
from typing import Optional, Tuple
import datetime

THIS_DIR = os.path.dirname(os.path.abspath(__file__))

REPO_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
"""Root path to the repo."""

URI_PREFIX = "ghcr.io/idaholab/moose-containers/"
"""URI prefix for container pushes."""

CONTAINERS_FILE = "containers.yml"
"""The path to the containers.yml file, relative to the repo root."""

PACKAGES_FILE = "packages.yml"
"""The path to the packages.yml file, relative to the repo root."""

GITHUB_ACTION = os.environ.get("GITHUB_ACTIONS") == "true"
"""Whether or not we're executed in a github action."""

REPO = "idaholab/moose-containers"
"""The GitHub repository."""


class ContainersException(Exception):
    def __init__(self, name: str, message: str):
        super().__init__(f"{CONTAINERS_FILE}: {name}: {message}")


def git_show(path: str, ref: str) -> str:
    """Use git to show a file at the given reference."""
    cmd = ["git", "show", f"{ref}:{path}"]
    return subprocess.check_output(cmd, cwd=REPO_ROOT, text=True)


class Container:
    """Data class for a single container to be built."""

    def __init__(self, name: str, tags: list[str], date: str):
        assert isinstance(name, str)
        assert isinstance(tags, list)
        assert all(isinstance(v, str) for v in tags)
        assert isinstance(date, str)

        self._name: str = name
        """Name of the container."""

        self._tags: list[str] = tags
        """Tags for the container."""

        try:
            date_parsed = datetime.datetime.strptime(date, "%Y%m%d").date()
        except Exception as e:
            raise ContainersException(name, f"date='{date}' is invalid") from e
        if date_parsed > datetime.date.today():
            raise ContainersException(name, f"date='{self.date}' is from the future")

        self._date: datetime.date = date
        """The date for this container."""

        self._raw_date: str = date
        """The raw string date for this container."""

        self._from_container: Optional["Container"] = None
        """The container this container is built from, if any."""

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
        return f"{'-'.join(tags)}-{self.date}"

    def get_uri(self, pr: Optional[int] = None, main: bool = False) -> str:
        """Get the URI for this container."""
        uri = URI_PREFIX
        if pr is not None:
            uri += f"pr-"
            assert not main
        elif main:
            uri += "main-"
        uri += f"{self.name}:"
        if pr is not None:
            uri += f"pr{pr}-"
        uri += self.tag
        return uri


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
        containers[name]._from_container = from_container

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


def container_url(name: str, pr: bool = False, main: bool = False) -> str:
    """Get the URL to a container."""
    assert pr != main
    prefix = "pr-" if pr else "main-"
    return f"https://github.com/idaholab/moose-containers/pkgs/container/moose-containers%2F{prefix}{name}"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Prepare container listing and changes."
    )

    parent = argparse.ArgumentParser(add_help=False)

    action_parser = parser.add_subparsers(dest="action", help="Action to perform")
    action_parser.required = True

    def add_common(parser: argparse.ArgumentParser):
        parser.add_argument("--github-token", type=str, help="The github token")

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


def github_get_pr_comment(pr: int, marker: str, github_token: str) -> Optional[str]:
    """Find a previous comment from this job by looking for our marker."""
    url = f"https://api.github.com/repos/{REPO}/issues/{pr}/comments"

    while url:
        response = requests.get(url, headers=get_github_headers(github_token))
        response.raise_for_status()
        comments = response.json()

        for comment in comments:
            if marker in comment["body"]:
                return comment["id"]

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

    if existing_id:
        github_delete_pr_comment(existing_id, github_token)

    url = f"https://api.github.com/repos/{REPO}/issues/{pr}/comments"
    payload = {"body": f"{marker}\n{body}"}
    response = requests.post(
        url, json=payload, headers=get_github_headers(github_token)
    )
    response.raise_for_status()
    print(f"Posted comment: {response.json()['id']}")


def github_container_exists(
    github_token: str,
    container: Container,
    pr: Optional[int] = None,
    main: bool = False,
):
    assert pr is not None or main
    assert (pr is not None) != main

    uri = container.get_uri(pr=pr, main=main)
    repo_and_tag = uri.split("/")[-1].split(":")
    repo = repo_and_tag[0]
    tag = repo_and_tag[1]

    url = f"https://ghcr.io/v2/idaholab/moose-containers/{repo}/manifests/{tag}"
    response = requests.get(url, headers=get_github_headers(github_token))
    return response.status_code == 200


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

    # Determine changed containers
    uris = {}
    changed = {}
    build_summary = []
    for name in sorted(current_containers):
        container = current_containers[name]
        tag = container.tag
        base_container = base_containers.get(name)

        build = base_container is None or tag != base_container.tag
        if (
            not build
            and GITHUB_ACTION
            and github_token
            and main
            and github_container_exists(main=main, github_token=github_token)
        ):
            print("::warning::Container does not exist on main; building")
            build = True

        if build:
            if base_container.date > container.date:
                raise ContainersException(name, "date moved back")
            uris[name] = container.get_uri(pr=pr, main=main)
            changed[name] = True
            url = container_url(name, pr=pr is not None, main=main)
            summary_name = f"[`{name}`]({url})"
            build_summary.append(
                (
                    summary_name,
                    f"`{base_container.tag}`" if base_container.tag else "",
                    f"`{tag}`",
                )
            )
        else:
            uris[name] = container.get_uri(main=True)
            changed[name] = False

    # Determine changed packages
    package_summary = []
    for name in sorted(packages):
        value = packages[name]
        base_value = base_packages.get(name)
        if base_value is None or value != base_value:
            package_summary.append((f"`{name}`", f"`{value}`", f"`{base_value}"))

    # Build summary table
    build_output = "## Builds\n\n"
    if build_summary:
        build_output += tabulate(
            build_summary, headers=["container", "base tag", "tag"], tablefmt="github"
        )
    else:
        build_output += "No containers to build"
    if GITHUB_ACTION:
        build_output += "\n\n"
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(build_output)
    print_section("Build summary", build_output)

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

    return build_output + packages_output


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
    containers, packages = load_current()
    raise Exception("not working yet")


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
