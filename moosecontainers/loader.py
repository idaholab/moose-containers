"""Loading of containers.yml and packages.yml."""

import datetime
import os
import subprocess
from collections.abc import Callable
from typing import Annotated, Any

import jinja2
import jinja2.sandbox
import pydantic
import yaml

from moosecontainers import config
from moosecontainers.container import Container, ContainersException


class ConfigError(Exception):
    """Exception for an invalid configuration file."""


# The configuration can come from an untrusted pull request (from a fork), and
# its values end up in image tags, paths and shell commands; limit them to
# characters that are safe in each
Name = Annotated[
    str, pydantic.StringConstraints(pattern=r"^[a-z0-9][a-z0-9.-]*$")
]
"""A container name or a Dockerfile directory."""

Tag = Annotated[str, pydantic.StringConstraints(pattern=r"^[A-Za-z0-9_.-]+$")]
"""A part of an image tag."""

BuildArgName = Annotated[
    str, pydantic.StringConstraints(pattern=r"^[A-Za-z_][A-Za-z0-9_]*$")
]
"""The name of a Docker build argument."""

BuildArgValue = Annotated[
    str, pydantic.StringConstraints(pattern=r"^[A-Za-z0-9_.:/+@=-]*$")
]
"""The value of a Docker build argument."""


class ContainerConfig(pydantic.BaseModel):
    """The configuration for a single container in containers.yml."""

    model_config = pydantic.ConfigDict(strict=True, extra="forbid", frozen=True)

    tags: list[Tag]
    """Tags for the container."""

    date: str
    """The date for the container (YYYYMMDD)."""

    release: bool = False
    """Whether or not this container should be released."""

    dockerfile: Name | None = None
    """The Dockerfile directory, relative to the layer's context."""

    build_args: dict[BuildArgName, BuildArgValue] = pydantic.Field(
        default_factory=dict, alias="build-args"
    )
    """Extra build arguments for the Dockerfile."""

    from_: Name | None = pydantic.Field(default=None, alias="from")
    """The name of the container this container is built from, if any."""

    @pydantic.field_validator("date")
    @classmethod
    def _check_date(cls, value: str) -> str:
        """Check that the date is a valid YYYYMMDD date, not in the future."""
        try:
            date = datetime.datetime.strptime(value, "%Y%m%d").date()
        except ValueError as e:
            raise ValueError(f"'{value}' is not a valid YYYYMMDD date") from e
        if date > datetime.date.today():
            raise ValueError(f"'{value}' is from the future")
        return value


ContainersConfig = pydantic.RootModel[dict[Name, ContainerConfig]]
"""The configuration in containers.yml."""

PackagesConfig = pydantic.RootModel[dict[Name, Tag]]
"""The configuration in packages.yml."""


def _find_node(
    loader: yaml.SafeLoader, node: yaml.Node | None, loc: tuple
) -> yaml.Node | None:
    """Find the deepest YAML node that matches a pydantic error location."""
    key_node = None
    for item in loc:
        if item == "[key]":
            return key_node
        if isinstance(node, yaml.MappingNode):
            matches = [
                (k, v)
                for k, v in node.value
                if loader.construct_object(k, deep=True) == item
            ]
            if not matches:
                return node
            key_node, node = matches[-1]
        elif isinstance(node, yaml.SequenceNode):
            key_node, node = None, node.value[item]
        else:
            return node
    return node


def _location(node: yaml.Node | None, filename: str) -> str:
    """Get the filename:line:column location of a YAML node."""
    if node is None:
        return filename
    mark = node.start_mark
    return f"{filename}:{mark.line + 1}:{mark.column + 1}"


def load_yaml[T: pydantic.BaseModel](
    contents: str, filename: str, model: type[T]
) -> tuple[T, Callable[[tuple], str]]:
    """Load and validate YAML contents with the given model.

    Returns the validated model and a function for getting the location
    (filename:line:column) of an error location within the contents.

    Raises a ConfigError with the location of any error.
    """
    loader = yaml.SafeLoader(contents)
    loader.name = filename
    try:
        try:
            node = loader.get_single_node()
            data: Any = None
            if node is not None:
                data = loader.construct_document(node)
        except yaml.YAMLError as e:
            raise ConfigError(str(e)) from e

        def locate(loc: tuple) -> str:
            return _location(_find_node(loader, node, loc), filename)

        try:
            return model.model_validate(data), locate
        except pydantic.ValidationError as e:
            messages = []
            for error in e.errors(include_url=False):
                loc = error["loc"]
                path = ".".join(str(v) for v in loc if v != "[key]")
                # Point at the unexpected key itself, not its value
                if error["type"] == "extra_forbidden":
                    loc = (*loc, "[key]")
                prefix = f"{locate(loc)}: {path}" if path else locate(loc)
                messages.append(f"{prefix}: {error['msg']}")
            raise ConfigError("\n".join(messages)) from e
    finally:
        loader.dispose()


def git_show(path: str, ref: str) -> str:
    """Use git to show a file at the given reference."""
    cmd = ["git", "show", f"{ref}:{path}"]
    return subprocess.check_output(cmd, cwd=config.REPO_ROOT, text=True)


def load_packages(contents: str, filename: str) -> dict[str, str]:
    """Load and validate the contents of a packages.yml."""
    packages, _ = load_yaml(contents, filename, PackagesConfig)
    return dict(packages.root)


def load_containers(
    template: jinja2.FileSystemLoader | str,
    packages: dict[str, str],
    filename: str = config.CONTAINERS_FILE,
) -> dict[str, Container]:
    """Render a containers.yml template with the given packages input."""
    # Sandboxed, as the template can come from an untrusted pull request
    env = jinja2.sandbox.SandboxedEnvironment()
    if isinstance(template, jinja2.FileSystemLoader):
        env.loader = template
        template = env.get_template(config.CONTAINERS_FILE)
    else:
        template = env.from_string(template)

    # Helper for package("") function in jinja
    def get_package(name: str):
        value = packages.get(name)
        if value is None:
            raise KeyError(f"Unknown package {name} in packages.yml")
        return value

    # Render and validate containers.yml; rendering preserves the lines
    # of the template, so locations refer to the template itself
    output = template.render(package=get_package)
    result, locate = load_yaml(output, filename, ContainersConfig)

    containers = {
        name: Container(
            name=f"moose-{name}",
            tags=list(values.tags),
            date=values.date,
            release=values.release,
            dockerfile=values.dockerfile,
            build_args=dict(values.build_args),
        )
        for name, values in result.root.items()
    }

    # Setup container_from
    for name, values in result.root.items():
        if values.from_ is None:
            continue
        from_container = containers.get(values.from_)
        if from_container is None:
            raise ConfigError(
                f"{locate((name, 'from'))}: {name}.from: "
                f"container {values.from_} not found"
            )
        containers[name].set_from_container(from_container)

    return containers


def load_current() -> tuple[dict[str, Container], dict[str, str]]:
    """Render the current containers.yml with the current packages.yml."""
    # Load packages config
    with open(os.path.join(config.REPO_ROOT, config.PACKAGES_FILE)) as f:
        packages = load_packages(f.read(), config.PACKAGES_FILE)

    containers_template = jinja2.FileSystemLoader(config.REPO_ROOT)
    containers = load_containers(containers_template, packages)

    # Only the current containers need to be buildable
    for container in containers.values():
        if not os.path.isfile(os.path.join(config.REPO_ROOT, container.file)):
            raise ContainersException(
                container.name, f"{container.file} does not exist"
            )

    return containers, packages


def load_previous(ref: str) -> tuple[dict[str, Container], dict[str, str]]:
    """Render a previous containers.yml template at the given git reference."""
    packages = load_packages(
        git_show(config.PACKAGES_FILE, ref), f"{ref}:{config.PACKAGES_FILE}"
    )
    containers_template = git_show(config.CONTAINERS_FILE, ref)
    containers = load_containers(
        containers_template, packages, f"{ref}:{config.CONTAINERS_FILE}"
    )
    return containers, packages
