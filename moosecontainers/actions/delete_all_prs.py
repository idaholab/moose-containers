"""The delete_all_prs action."""

import argparse
import re

from moosecontainers.arguments import add_dry_run, add_github_token
from moosecontainers.delete import delete_containers
from moosecontainers.github import GitHubContainer


def add_parser(subparsers: argparse._SubParsersAction):
    """Add the parser for this action."""
    parser = subparsers.add_parser(
        "delete_all_prs", help="Delete all pull request images."
    )
    add_github_token(parser, required=True)
    add_dry_run(parser)


def condition(github_container: GitHubContainer) -> bool:
    """Whether or not the given container should be deleted."""
    return (
        len(github_container.tags) == 1
        and re.match("^pr[0-9]+-", github_container.tags[0]) is not None
    )


def run(args: argparse.Namespace):
    """Perform the delete_all_prs action."""
    delete_containers(condition, args.github_token, args.dry_run, False)
