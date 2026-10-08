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

3. **The workflows are written by hand.** They don't read `containers.yml` for you.
   - New container: in `build.yml`, add its `changed-*` and `uri-*` outputs to `prepare`,
     a build job, and an entry in `finalize`.
   - New container with `release: true`: also add its `from-*`/`to-*` outputs, a job, and
     a `finalize` entry in `release.yml`.
   - New package: add a `package-*` output to `prepare` in `build.yml`.

4. **The Docker build context is `docker/<layer>`.** `COPY` and `--mount` paths are
   relative to it, e.g. `files/install_mpich.bash` or `rocky8-oneapi/files/oneAPI.repo`.

5. **Keep the `/moose_env.sh` pattern.** Each Dockerfile appends a `# From ${CONTAINER_NAME}`
   line plus its environment to `/moose_env.sh`, and checks that the installed version
   is the expected one. Do the same in new or edited Dockerfiles.

6. **Check your changes locally.**
   - `uv run python .github/scripts/ci.py prepare_push origin/main` shows which containers
     would build and which packages changed. Without a token it skips registry checks.
   - `uv run ruff check` and `uv run ruff format` for Python.

7. **Keep the README current.**
   - The "Released images" table is generated. After changing `packages.yml` or
     `containers.yml`, run `uv run python .github/scripts/ci.py readme`. The PR build
     fails if you forget.
   - The example tag in the "Versioning" section is written by hand. If you change
     versions used by `moose-mpi-ubuntu24-gcc`, update it too.
