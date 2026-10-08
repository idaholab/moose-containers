"""The post_release action."""

import argparse

from moosecontainers.arguments import add_github_token
from moosecontainers.post import post_action


def add_parser(subparsers: argparse._SubParsersAction):
    """Add the parser for this action."""
    parser = subparsers.add_parser(
        "post_release",
        help="Perform the post-release action (check if containers exist).",
    )
    add_github_token(parser)


def run(args: argparse.Namespace):
    """Perform the post_release action."""
    post_action(args.github_token, release=True)
