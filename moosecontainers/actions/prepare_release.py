"""The prepare_release action."""

import argparse
import json
import sys
from copy import deepcopy

from moosecontainers import github
from moosecontainers.arguments import add_github_token
from moosecontainers.loader import load_current
from moosecontainers.output import build_summary_table, write_outputs


def add_parser(subparsers: argparse._SubParsersAction):
    """Add the parser for this action."""
    parser = subparsers.add_parser(
        "prepare_release", help="Perform the release action."
    )
    add_github_token(parser, required=True)


def run(args: argparse.Namespace):
    """Perform the prepare_release action."""
    containers, _ = load_current()

    # Get a ghcr token for determining package existence
    ghcr_token = github.ghcr_token(args.github_token)

    # Whether or not we're missing containers for a release
    missing_containers = False

    releases = []
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

        # Skip containers already released
        if github.container_exists(container.repo, container.tag, ghcr_token):
            continue

        # Check for existence of main container
        if not github.container_exists(
            main_container.repo, main_container.tag, ghcr_token
        ):
            print(
                f"::error::Main container {main_container.uri} does not exist"
            )
            missing_containers = True

        releases.append(
            {
                "name": name,
                "from": main_container.uri,
                "to": container.uri,
            }
        )
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

    # Do github output; the matrix for the release job
    write_outputs({"releases": json.dumps(releases)})
