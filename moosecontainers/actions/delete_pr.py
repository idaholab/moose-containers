"""The delete_pr action."""

import argparse
import sys

from moosecontainers.arguments import add_dry_run, add_github_token, add_pr
from moosecontainers.container import Container
from moosecontainers.delete import delete_containers
from moosecontainers.github import GitHubContainer


def add_parser(subparsers: argparse._SubParsersAction):
    """Add the parser for this action."""
    parser = subparsers.add_parser(
        "delete_pr", help="Delete pull request images."
    )
    add_github_token(parser, required=True)
    add_dry_run(parser)
    add_pr(parser)
    parser.add_argument(
        "--only-cache",
        action="store_true",
        help="Only delete the cache, not the final images.",
    )
    parser.add_argument(
        "--only-images",
        action="store_true",
        help="Only delete the final images, not the cache.",
    )
    parser.add_argument(
        "--allow-missing-repos",
        action="store_true",
        help="Allow repositories to not exist.",
    )


def run(args: argparse.Namespace):
    """Perform the delete_pr action."""
    only_cache = args.only_cache
    only_images = args.only_images

    if only_cache and only_images:
        print("ERROR: Cannot supply --only-cache and --only-images")
        sys.exit(1)

    prefix = Container.get_pr_tag_prefix(args.pr)
    cache_tag = f"{prefix}cache"

    def condition(github_container: GitHubContainer) -> bool:
        if len(github_container.tags) == 0:
            return False
        tag = github_container.tags[0]

        if only_cache:
            return tag == cache_tag
        if only_images:
            return tag != cache_tag and tag.startswith(prefix)
        return tag.startswith(prefix)

    delete_containers(
        condition, args.github_token, args.dry_run, args.allow_missing_repos
    )
