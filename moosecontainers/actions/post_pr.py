"""The post_pr action."""

import argparse

from moosecontainers.arguments import add_github_token, add_pr
from moosecontainers.post import post_action


def add_parser(subparsers: argparse._SubParsersAction):
    """Add the parser for this action."""
    parser = subparsers.add_parser(
        "post_pr",
        help=(
            "Perform the post-pull request action (check if containers exist)."
        ),
    )
    add_pr(parser)
    add_github_token(parser)


def run(args: argparse.Namespace):
    """Perform the post_pr action."""
    post_action(args.github_token, pr=args.pr)
