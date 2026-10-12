"""Console and GitHub action output."""

import os

from tabulate import tabulate


def in_github_action() -> bool:
    """Whether or not we're executed in a GitHub action."""
    return os.environ.get("GITHUB_ACTIONS") == "true"


def print_section(title: str, contents: str | list[str]):
    """Print a section of output, grouped when in a GitHub action."""
    github = in_github_action()

    if github:
        print(f"::group::{title}")
    else:
        print(f"-- {title}\n")

    if isinstance(contents, str):
        print(contents)
    else:
        print("\n".join(contents))

    if github:
        print("::endgroup::")
    else:
        print()


def build_summary_table(
    title: str, rows: list[tuple], headers: list[str], empty: str
) -> str:
    """Build a markdown summary section with a table, or a note if empty.

    Also prints it and, in a GitHub action, appends it to the step summary.
    """
    output = f"## {title}\n\n"
    if rows:
        output += tabulate(rows, headers=headers, tablefmt="github")
    else:
        output += empty
    if in_github_action():
        output += "\n\n"
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(output)
    print_section(f"{title} summary", output)
    return output


def write_outputs(outputs: dict[str, str]):
    """Print the given step outputs and write them in a GitHub action."""
    lines = [f"{k}={v}" for k, v in outputs.items()]
    if in_github_action():
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.writelines(f"{line}\n" for line in lines)
    print_section("Output", lines)
