"""A single container to be built."""

import datetime

from moosecontainers.config import (
    CONTAINERS_FILE,
    FULL_REPO,
    STAGING_PREFIX,
    URI_PREFIX,
)


class ContainersException(Exception):
    """Exception for an error in the containers file."""

    def __init__(self, name: str, message: str):
        """Initialize the exception for the given container name."""
        super().__init__(f"{CONTAINERS_FILE}: {name}: {message}")


class Container:
    """Data class for a single container to be built."""

    def __init__(
        self,
        name: str,
        tags: list[str],
        date: str,
        release: bool = False,
        dockerfile: str | None = None,
        build_args: dict[str, str] | None = None,
    ):
        """Initialize the container."""
        assert isinstance(name, str)
        assert isinstance(tags, list)
        assert all(isinstance(v, str) for v in tags)
        assert isinstance(date, str)
        assert isinstance(release, bool)
        assert dockerfile is None or isinstance(dockerfile, str)
        build_args = build_args or {}
        if not isinstance(build_args, dict) or not all(
            isinstance(k, str) and isinstance(v, str)
            for k, v in build_args.items()
        ):
            raise ContainersException(name, "build-args must map str to str")

        self._name: str = name
        """Name of the container."""

        self._tags: list[str] = tags
        """Tags for the container."""

        try:
            date_parsed = datetime.datetime.strptime(date, "%Y%m%d").date()
        except Exception as e:
            raise ContainersException(name, f"date='{date}' is invalid") from e
        if date_parsed > datetime.date.today():
            raise ContainersException(name, f"date='{date}' is from the future")

        self._date: datetime.date = date_parsed
        """The date for this container."""

        self._raw_date: str = date
        """The raw string date for this container."""

        self._release: bool = release
        """Whether or not this container should be released."""

        self._from_container: Container | None = None
        """The container this container is built from, if any."""

        self._pr_tag: int | None = None
        """Whether or not this container has a PR name/tag. Used in the URI."""

        self._main_tag: bool = False
        """Whether or not this container has a main name/tag (for the URI)."""

        self._release_tag: bool = False
        """Whether or not this container has a release tag (for the URI)."""

        self._dockerfile: str | None = dockerfile
        """The Dockerfile directory, relative to the layer's context."""

        self._build_args: dict[str, str] = build_args
        """Extra build arguments for the Dockerfile."""

    @property
    def name(self) -> str:
        """The name of the container."""
        return self._name

    @property
    def date(self) -> datetime.date:
        """The date for the container."""
        return self._date

    @property
    def raw_date(self) -> str:
        """The raw (string) date for this container."""
        return self._raw_date

    @property
    def release(self) -> bool:
        """Whether or not this container should be released."""
        return self._release

    @property
    def layer(self) -> str:
        """The layer (base, compiler, mpi) that this container is in."""
        return self.name.removeprefix("moose-").split("-")[0]

    @property
    def context(self) -> str:
        """The Docker build context, relative to the repo root."""
        return f"docker/{self.layer}"

    @property
    def file(self) -> str:
        """The path to the Dockerfile, relative to the repo root."""
        if self._dockerfile is None:
            raise ContainersException(self.name, "dockerfile is not set")
        return f"{self.context}/{self._dockerfile}/Dockerfile"

    @property
    def build_args(self) -> dict[str, str]:
        """The build arguments, including BUILD_FROM for a parent container."""
        args = {}
        if self.from_container is not None:
            args["BUILD_FROM"] = self.from_container.uri
        args.update(self._build_args)
        return args

    @property
    def from_container(self) -> Container | None:
        """The container this container is built from, if any."""
        return self._from_container

    @staticmethod
    def get_pr_tag_prefix(pr_num: int) -> str:
        """Get the tag prefix for a pull request container."""
        return f"pr{pr_num}-"

    @staticmethod
    def get_main_tag_prefix() -> str:
        """Get the tag prefix for a main event container."""
        return "main-"

    @property
    def raw_tag(self) -> str:
        """Get the raw (without any prefixes) tag for this container."""
        parent_tags: list[str] = []
        parent = self.from_container
        while parent is not None:
            parent_tags = parent._tags + parent_tags
            parent = parent.from_container

        return "-".join(parent_tags + self._tags + [self.raw_date])

    @property
    def tag(self) -> str:
        """Get the tag for this container."""
        if self._pr_tag is not None:
            return f"{self.get_pr_tag_prefix(self._pr_tag)}{self.raw_tag}"
        if self._main_tag:
            return f"{self.get_main_tag_prefix()}{self.raw_tag}"
        return self.raw_tag

    @property
    def repo(self) -> str:
        """Get the repo for this container."""
        if self._pr_tag is not None or self._main_tag:
            return f"{STAGING_PREFIX}{self.name}"
        return self.name

    @property
    def uri(self) -> str:
        """Get the URI for this container."""
        return f"{URI_PREFIX}/{self.repo}:{self.tag}"

    @property
    def url(self) -> str:
        """Get the URL on GitHub for this repo."""
        return f"https://github.com/{FULL_REPO}/pkgs/container/moose-containers%2F{self.repo}"

    def set_from_container(self, from_container: Container):
        """Set the from container. Can only be called once."""
        assert isinstance(from_container, Container)
        assert self._from_container is None
        self._from_container = from_container

    def _assert_no_tag(self):
        """Assert that no PR, main, or release tag is set."""
        assert self._pr_tag is None
        assert not self._main_tag
        assert not self._release_tag

    def set_pr_tag(self, pr: int):
        """Set the pull request tag. Can only be called once."""
        assert isinstance(pr, int)
        self._assert_no_tag()
        self._pr_tag = pr

    def set_main_tag(self):
        """Set the main tag. Can only be called once."""
        self._assert_no_tag()
        self._main_tag = True

    def set_release_tag(self):
        """Set the release tag. Can only be called once."""
        self._assert_no_tag()
        self._release_tag = True
