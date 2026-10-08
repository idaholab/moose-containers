"""Checks that the expected containers exist after a build."""

import sys
from copy import deepcopy

from moosecontainers import github
from moosecontainers.container import Container
from moosecontainers.loader import load_current


def post_action(
    github_token: str, pr: int | None = None, release: bool = False
):
    """Check that the expected containers exist after a build."""
    ghcr_token = github.ghcr_token(github_token)

    containers, _ = load_current()

    main_containers = deepcopy(containers)
    for container in main_containers.values():
        container.set_main_tag()

    pr_containers = {}
    if pr is not None:
        pr_containers = deepcopy(containers)
        for container in pr_containers.values():
            container.set_pr_tag(pr)

    release_containers = {}
    if release:
        release_containers = deepcopy(containers)
        for container in release_containers.values():
            container.set_release_tag()

    def check_exists(name: str, containers: dict[str, Container]) -> bool:
        other_container = containers.get(name)
        if other_container is None:
            return False
        print(f"  {other_container.uri}... ", end="")
        if github.container_exists(
            other_container.repo, other_container.tag, ghcr_token
        ):
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
            if check_exists(name, pr_containers):
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
