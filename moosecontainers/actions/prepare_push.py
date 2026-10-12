"""The prepare_push action."""

import argparse

from moosecontainers.arguments import add_base_ref, add_github_token
from moosecontainers.prepare import prepare_with_base


def add_parser(subparsers: argparse._SubParsersAction):
    """Add the parser for this action."""
    parser = subparsers.add_parser(
        "prepare_push", help="Perform the push action."
    )
    add_base_ref(parser)
    add_github_token(parser)


def run(args: argparse.Namespace):
    """Perform the prepare_push action."""
    prepare_with_base(args.base_ref, main=True, github_token=args.github_token)
