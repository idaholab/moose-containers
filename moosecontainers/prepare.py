"""Preparation of a build by comparing against a base reference."""

import json
from copy import deepcopy

from moosecontainers import github
from moosecontainers.container import ContainersException
from moosecontainers.loader import load_current, load_previous
from moosecontainers.output import build_summary_table, write_outputs


def prepare_with_base(
    base_ref: str,
    pr: int | None = None,
    main: bool = False,
    github_token: str | None = None,
) -> str:
    """Prepare a build by comparing against the given base reference."""
    assert (pr is not None) != main

    current_containers, packages = load_current()
    base_containers, base_packages = load_previous(base_ref)

    # Set main state for base containers
    for container in base_containers.values():
        container.set_main_tag()

    # Get a ghcr token for determining package existence
    ghcr_token = None
    if github_token:
        ghcr_token = github.ghcr_token(github_token)

    # Determine changed containers
    changed = {}
    build_summary = []
    unreleased_summary = []
    for name in sorted(current_containers):
        container = current_containers[name]
        base_container = base_containers.get(name)

        # Keep track of unreleased containers
        if container.release and ghcr_token:
            release_container = deepcopy(container)
            release_container.set_release_tag()
            if not github.container_exists(
                release_container.repo, release_container.tag, ghcr_token
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
            and not github.container_exists(
                container.repo, container.tag, ghcr_token
            )
        ):
            print(
                f"::warning::Container {container.uri} does not exist; building"
            )
            build = True

        changed[name] = build
        if build:
            summary_name = f"[`{container.name}`]({container.url})"
            build_summary.append(
                (
                    summary_name,
                    f"`{base_container.tag}`" if base_container else "",
                    f"`{container.uri}`",
                )
            )

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

    # Everything a build job needs, for the generated build.yml jobs. Built
    # after the loop so that each parent's URI (in BUILD_FROM) is final.
    build_info = {
        name: {
            "changed": changed[name],
            "uri": container.uri,
            "context": container.context,
            "file": container.file,
            "build_args": "\n".join(
                f"{k}={v}" for k, v in container.build_args.items()
            ),
        }
        for name, container in current_containers.items()
    }

    # Do github output
    write_outputs({"containers": json.dumps(build_info, sort_keys=True)})

    return build_output + packages_output + unreleased_output
