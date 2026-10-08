"""The command line interface."""

import argparse

from moosecontainers.actions import (
    delete_all_prs,
    delete_pr,
    delete_untagged,
    post_pr,
    post_push,
    post_release,
    prepare_pr,
    prepare_push,
    prepare_release,
    readme,
    workflows,
)

ACTIONS = {
    "prepare_pr": prepare_pr,
    "prepare_push": prepare_push,
    "prepare_release": prepare_release,
    "post_pr": post_pr,
    "post_push": post_push,
    "post_release": post_release,
    "delete_untagged": delete_untagged,
    "delete_pr": delete_pr,
    "delete_all_prs": delete_all_prs,
    "workflows": workflows,
    "readme": readme,
}
"""The actions (name -> module) that can be performed."""


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser(
        prog="moosecontainers",
        description="CI utilities for building MOOSE containers.",
    )
    subparsers = parser.add_subparsers(
        dest="action", help="Action to perform", required=True
    )
    for module in ACTIONS.values():
        module.add_parser(subparsers)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None):
    """Run the action given on the command line."""
    args = parse_args(argv)
    ACTIONS[args.action].run(args)
