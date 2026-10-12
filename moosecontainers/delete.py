"""Deletion of staging containers from the GitHub container registry."""

import sys
from collections.abc import Callable

from moosecontainers import github
from moosecontainers.config import STAGING_PREFIX
from moosecontainers.github import GitHubContainer, GitHubContainerRepoMissing
from moosecontainers.loader import load_current


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
            github_containers = github.get_containers(name, token)
        except GitHubContainerRepoMissing:
            missing_repos.append(name)
            print(f"  {container.repo} does not exist")
            continue

        for github_container in github_containers:
            if "latest" in github_container.tags:
                continue

            assert len(github_container.tags) < 2, "Should have one or no tags"

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
                    github.delete_container(github_container, token)
                    num_deleted += 1

    print(f"\nDeleted {num_deleted} image(s)")

    if missing_repos:
        print(
            "\nThe following container repo(s) do not exist:\n\n"
            + "\n".join(missing_repos)
        )
        if not allow_missing_repos:
            sys.exit(1)
