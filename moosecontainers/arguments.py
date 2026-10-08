"""Command line arguments shared between actions."""

import argparse


def add_github_token(parser: argparse.ArgumentParser, required: bool = False):
    """Add the --github-token argument."""
    parser.add_argument(
        "--github-token",
        type=str,
        help="The github token",
        required=required,
    )


def add_dry_run(parser: argparse.ArgumentParser):
    """Add the --dry-run argument."""
    parser.add_argument(
        "--dry-run", action="store_true", help="Perform a dry run."
    )


def add_base_ref(parser: argparse.ArgumentParser):
    """Add the base_ref positional argument."""
    parser.add_argument(
        "base_ref",
        type=str,
        help="The base git reference to compare against.",
    )


def add_pr(parser: argparse.ArgumentParser):
    """Add the pr positional argument."""
    parser.add_argument("pr", type=int, help="The pull request number.")


def add_check(parser: argparse.ArgumentParser, help: str):
    """Add the --check argument."""
    parser.add_argument("--check", action="store_true", help=help)
