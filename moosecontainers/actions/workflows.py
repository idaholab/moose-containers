"""The workflows action."""

import argparse
import os
import sys

import jinja2

from moosecontainers import config
from moosecontainers.arguments import add_check
from moosecontainers.container import ContainersException
from moosecontainers.loader import load_current


def add_parser(subparsers: argparse._SubParsersAction):
    """Add the parser for this action."""
    parser = subparsers.add_parser(
        "workflows", help="Generate the workflows from their templates."
    )
    add_check(parser, "Only check that the workflows are up to date.")


def render(template_path: str) -> str:
    """Render a workflow template with the current containers.

    The template uses [[ ]], [% %] and [# #] instead of jinja's defaults,
    so that GitHub's own ${{ }} expressions can be written as is.
    """
    containers, _ = load_current()
    parents = {
        name: next(
            k for k, v in containers.items() if v is container.from_container
        )
        if container.from_container is not None
        else None
        for name, container in containers.items()
    }

    # Order so that every parent comes before its children
    ordered: list[str] = []
    while len(ordered) < len(containers):
        ready = [
            name
            for name in containers
            if name not in ordered
            and (parents[name] is None or parents[name] in ordered)
        ]
        if not ready:
            raise ContainersException(
                ", ".join(n for n in containers if n not in ordered),
                "from containers form a cycle",
            )
        ordered.extend(ready)

    # Containers that nothing is built from; finalize waits on these
    leaves = [name for name in ordered if name not in parents.values()]

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(config.REPO_ROOT),
        variable_start_string="[[",
        variable_end_string="]]",
        block_start_string="[%",
        block_end_string="%]",
        comment_start_string="[#",
        comment_end_string="#]",
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        undefined=jinja2.StrictUndefined,
    )
    template = env.get_template(template_path)
    return template.render(
        containers=[(name, parents[name]) for name in ordered], leaves=leaves
    )


def run(args: argparse.Namespace):
    """Perform the workflows action."""
    out_of_date = []
    for template_path, workflow_path in config.WORKFLOWS.items():
        rendered = render(template_path)
        path = os.path.join(config.REPO_ROOT, workflow_path)
        contents = None
        if os.path.exists(path):
            with open(path) as f:
                contents = f.read()

        if rendered == contents:
            print(f"{workflow_path} is up to date")
            continue

        if args.check:
            out_of_date.append(workflow_path)
            continue

        with open(path, "w") as f:
            f.write(rendered)
        print(f"Updated {workflow_path}")

    if out_of_date:
        print(
            "ERROR: The following workflow(s) are out of date:\n\n  "
            + "\n  ".join(out_of_date)
            + f"\n\nrun:\n\n  {config.COMMAND} workflows"
        )
        sys.exit(1)
