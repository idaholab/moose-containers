# AGENTS.md

See [README.md](README.md) for what this repository does.

## Rules

1. **Containers only build when their tag changes.** Editing a Dockerfile or helper script
   does nothing on its own. To rebuild, bump the container's `date` in `containers.yml`
   (`YYYYMMDD`, not in the future, never moving backward). Children don't include their
   parent's date, so bump their dates too if they should rebuild.

2. **Some versions are not in `packages.yml`.** Changing these also needs a date bump:
   - The Rocky `FROM` lines in `docker/base/rocky8` and `docker/base/rocky9` are pinned.
     Update them along with `rocky8`/`rocky9` in `packages.yml`, or the build fails.
   - `VALGRIND_VERSION` is set in each compiler Dockerfile.

3. **`build.yml` is generated; don't edit it.** Edit `.github/templates/build.yml.j2`
   or `containers.yml`, then run `uv run moosecontainers workflows`. The PR
   build fails if `build.yml` is out of date.
   - New container: add it to `containers.yml` with its `from`, `dockerfile` (a directory
     under `docker/<layer>`), `build-args`, `tags` and `date`, then regenerate.
     Don't list `BUILD_FROM` or `CONTAINER_NAME`; they are filled in for you.
   - New package: add it to `packages.yml` and use it with `{{ package("...") }}`.
     No workflow changes are needed.
   - `release.yml` is written by hand but needs no changes; it releases every
     `release: true` container.

4. **The Docker build context is `docker/<layer>`.** `COPY` and `--mount` paths are
   relative to it, e.g. `files/install_mpich.bash` or `rocky8-oneapi/files/oneAPI.repo`.

5. **Keep the `/moose_env.sh` pattern.** Each Dockerfile appends a `# From ${CONTAINER_NAME}`
   line plus its environment to `/moose_env.sh`, and checks that the installed version
   is the expected one. Do the same in new or edited Dockerfiles.

6. **Check your changes locally.**
   - `uv run moosecontainers prepare_push origin/main` shows which containers
     would build and which packages changed. Without a token it skips registry checks.
   - `uv run ruff check` and `uv run ruff format` for Python.
   - `uv run pytest` for the `moosecontainers` tests. Coverage must stay at 100%.
   - `uvx --from actionlint-py actionlint` for the workflows.

7. **The CI logic is the `moosecontainers` package.** Run it with `uv run moosecontainers <action>`.
   - Each command line action is its own module in `moosecontainers/actions/`, with an
     `add_parser()` for its arguments and a `run()`. Register new actions in `cli.py`.
   - Tests mirror the package: `moosecontainers/foo.py` is tested by `tests/test_foo.py`,
     and `moosecontainers/actions/foo.py` by `tests/actions/test_foo.py`.
   - Tests never make real HTTP requests. They're mocked with `responses`, and any
     request that isn't mocked fails. `git` runs for real, in a temporary repo.

8. **Keep the README current.**
   - The "Released images" table is generated. After changing `packages.yml` or
     `containers.yml`, run `uv run moosecontainers readme`. The PR build
     fails if you forget.
   - The example tag in the "Versioning" section is written by hand. If you change
     versions used by `moose-mpi-ubuntu24-gcc`, update it too.
