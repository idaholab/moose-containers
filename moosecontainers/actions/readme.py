"""The readme action."""

import argparse
import os
import re
import sys

from tabulate import tabulate

from moosecontainers import config
from moosecontainers.arguments import add_check
from moosecontainers.loader import load_current


def add_parser(subparsers: argparse._SubParsersAction):
    """Add the parser for this action."""
    parser = subparsers.add_parser(
        "readme", help=f"Update the release table in {config.README_FILE}."
    )
    add_check(parser, "Only check that the table is up to date.")


def build_releases() -> str:
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


def run(args: argparse.Namespace):
    """Perform the readme action."""
    path = os.path.join(config.REPO_ROOT, config.README_FILE)
    with open(path) as f:
        contents = f.read()

    start, end = config.README_START, config.README_END
    pattern = re.compile(f"{re.escape(start)}.*?{re.escape(end)}", re.DOTALL)
    if pattern.search(contents) is None:
        print(f"ERROR: {config.README_FILE} is missing {start} / {end}")
        sys.exit(1)

    block = f"{start}\n{build_releases()}\n{end}"
    updated = pattern.sub(lambda _: block, contents)

    if updated == contents:
        print(f"{config.README_FILE} is up to date")
        return

    if args.check:
        print(
            f"ERROR: {config.README_FILE} release table is out of date; "
            f"run:\n\n  {config.COMMAND} readme"
        )
        sys.exit(1)

    with open(path, "w") as f:
        f.write(updated)
    print(f"Updated {config.README_FILE}")
