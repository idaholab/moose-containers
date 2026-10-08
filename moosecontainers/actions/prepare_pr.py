"""The prepare_pr action."""

import argparse

from moosecontainers import github
from moosecontainers.arguments import add_base_ref, add_github_token, add_pr
from moosecontainers.output import in_github_action
from moosecontainers.prepare import prepare_with_base

MARKER = "<!-- prepare summary -->"
"""Marker for finding a previous pull request comment."""


def add_parser(subparsers: argparse._SubParsersAction):
    """Add the parser for this action."""
    parser = subparsers.add_parser(
        "prepare_pr", help="Perform the pull request action."
    )
    add_pr(parser)
    add_base_ref(parser)
    add_github_token(parser)


def run(args: argparse.Namespace):
    """Perform the prepare_pr action."""
    pr = args.pr
    github_token = args.github_token

    result = prepare_with_base(args.base_ref, pr, github_token=github_token)

    # Pull request comment
    if in_github_action() and github_token:
        print("::group::Post pull request comment")
        github.post_pr_comment(pr, result, MARKER, github_token)
        print("::endgroup::")
