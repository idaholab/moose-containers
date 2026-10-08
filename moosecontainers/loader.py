"""Loading of containers.yml and packages.yml."""

import os
import subprocess

import jinja2
import yaml

from moosecontainers import config
from moosecontainers.container import Container, ContainersException


def git_show(path: str, ref: str) -> str:
    """Use git to show a file at the given reference."""
    cmd = ["git", "show", f"{ref}:{path}"]
    return subprocess.check_output(cmd, cwd=config.REPO_ROOT, text=True)


def load_containers(
    template: jinja2.FileSystemLoader | str, packages: dict
) -> dict[str, Container]:
    """Render a containers.yml template with the given packages input."""
    if isinstance(template, jinja2.FileSystemLoader):
        env = jinja2.Environment(loader=template)
        template = env.get_template(config.CONTAINERS_FILE)
    else:
        template = jinja2.Template(template)

    # Helper for package("") function in jinja
    def get_package(name: str):
        value = packages.get(name)
        if value is None:
            raise KeyError(f"Unknown package {name} in packages.yml")
        return value

    # Render containers.yml
    output = template.render(package=get_package)
    result = yaml.safe_load(output)

    # Build Container objects without container_from
    from_values = {}

    def build_container(name: str, values: dict):
        if container_from := values.get("from"):
            from_values[name] = container_from
            del values["from"]
        if "build-args" in values:
            values["build_args"] = values.pop("build-args")
        return Container(name=f"moose-{name}", **values)

    containers = {k: build_container(k, v) for k, v in result.items()}

    # Setup container_from
    for name, from_value in from_values.items():
        from_container = containers.get(from_value)
        if from_container is None:
            raise ContainersException(
                name, f"from container {from_value} not found"
            )
        containers[name].set_from_container(from_container)

    return containers


def load_current() -> tuple[dict[str, Container], dict]:
    """Render the current containers.yml with the current packages.yml."""
    # Load packages config
    with open(os.path.join(config.REPO_ROOT, config.PACKAGES_FILE)) as f:
        packages = dict(yaml.safe_load(f))

    containers_template = jinja2.FileSystemLoader(config.REPO_ROOT)
    containers = load_containers(containers_template, packages)

    # Only the current containers need to be buildable
    for container in containers.values():
        if not os.path.isfile(os.path.join(config.REPO_ROOT, container.file)):
            raise ContainersException(
                container.name, f"{container.file} does not exist"
            )

    return containers, packages


def load_previous(ref: str) -> tuple[dict[str, Container], dict]:
    """Render a previous containers.yml template at the given git reference."""
    containers_template = git_show(config.CONTAINERS_FILE, ref)
    packages = yaml.safe_load(git_show(config.PACKAGES_FILE, ref))
    return load_containers(containers_template, packages), packages
