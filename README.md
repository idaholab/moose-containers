# moose-containers

This repository defines, builds, and publishes the base container images used by
[MOOSE](https://github.com/idaholab/moose) for continuous integration and deployment.

Each image provides a ready-to-use environment: an operating system, a compiler toolchain,
and MPI. MOOSE builds on top of these images, so it never has to set up these
dependencies itself. Every image is defined in this repository with exact, pinned versions.

All images are published to the GitHub Container Registry (ghcr.io) under
[`ghcr.io/idaholab/moose-containers`](https://github.com/orgs/idaholab/packages?repo_name=moose-containers).

## How it works

Two files control everything that gets built:

- **[`packages.yml`](packages.yml)** names every software version, such as the OS
  releases, CUDA, GCC, Clang, MPICH, OpenMPI, and Intel oneAPI.
  See [packages.yml](#packagesyml).
- **[`containers.yml`](containers.yml)** lists every container: what it builds on, its
  Dockerfile, and its tag. It refers to versions by name from `packages.yml`, so one
  version can be shared by many containers. See [containers.yml](#containersyml).

GitHub Actions works out which containers have changed and builds only those; see
[From pull request to release](#from-pull-request-to-release).

### Versioning

Each container's tag is made from its parents' versions, its own versions, and its date.
For example, the Ubuntu 24.04 GCC MPI image gets a tag like:

```
ghcr.io/idaholab/moose-containers/moose-mpi-ubuntu24-gcc:24.04-gcc14.2.0-mpich5.0.1-openmpi5.0.11-20260918
                                                         └─OS─┘ └compiler┘ └────────MPI────────┘ └─date─┘
```

**A container is built only when its tag changes.** Editing a Dockerfile or a helper
script does not trigger a build by itself. A container gets rebuilt when you:

- **Change a version in `packages.yml`.** Every container that uses that version gets a
  new tag, and so does every container built on top of it. The change flows down the
  whole dependency tree.
- **Change a container's `date` in `containers.yml`.** Use this to rebuild a container
  when no version changed, for example to pick up a Dockerfile change or OS updates.
  A parent's date is not part of its children's tags, so to rebuild the containers built
  on top of it as well, bump their dates too.

## Updating a container

Every change follows the same flow:

1. Make the change (see below). If it doesn't change a version, bump the `date` of each
   container that should be rebuilt; see [Versioning](#versioning).
2. Check locally which containers would build and which packages changed:

   ```bash
   uv run moosecontainers prepare_push origin/main
   ```

3. Open a pull request. Check the [summary comment](#pull-requests-buildyml) to confirm
   the right containers are being rebuilt, and wait for the builds to pass.
4. Merge the pull request. The `main` images are built.
5. Run the [Release](#release-releaseyml) workflow: a dry run first, then a real run.

What to change for common updates:

| Update | Change |
| --- | --- |
| A package version (GCC, MPICH, CUDA, ...) | The version in `packages.yml` |
| A Dockerfile or helper script | The files under `docker/<layer>`, plus the `date` of the containers that use them and their children |
| The Rocky Linux version | `rocky8`/`rocky9` in `packages.yml` **and** the pinned `FROM` line in `docker/base/rocky8` or `docker/base/rocky9`; the build fails if they don't match |
| Valgrind | `VALGRIND_VERSION` in each compiler Dockerfile, plus the `date` of the compiler containers (and their children) |
| A new container | An entry in [`containers.yml`](#containersyml), then `uv run moosecontainers workflows` to [regenerate `build.yml`](#ci-tooling) |
| A new package | An entry in [`packages.yml`](#packagesyml), used through [`package()`](#templating) |

After changing `packages.yml` or `containers.yml`, regenerate the
[released images](#released-images) table with `uv run moosecontainers readme`. The pull
request build fails if it is out of date.

## Configuration

Values must have exactly the type listed below, so versions and dates must be quoted.

### packages.yml

Maps a package name to its version:

```yaml
gcc-ubuntu24: "14.2.0"
```

| Key | Type | Description |
| --- | --- | --- |
| `<name>` | string | The version, used in `containers.yml` through [`package()`](#templating) |

### containers.yml

Maps a container name to its definition. The image is published as `moose-<name>`, and
the first part of the name is its [layer](#containers):

```yaml
compiler-ubuntu24-gcc:
  from: base-ubuntu24
  dockerfile: ubuntu-gcc
  build-args:
    GCC_VERSION: "{{ package("gcc-ubuntu24") }}"
  tags:
    - "gcc{{ package("gcc-ubuntu24") }}"
  date: "20260918"
```

| Key | Type | Required | Description |
| --- | --- | --- | --- |
| `tags` | list of strings | yes | Versions added to the [tag](#versioning), after the parents' tags |
| `date` | string | yes | `YYYYMMDD`; not in the future, and never moving backward |
| `dockerfile` | string | yes, for current containers | Directory under `docker/<layer>` that holds the `Dockerfile` |
| `from` | string | no | Name of the container in this file to build on |
| `build-args` | map of string to string | no | Build arguments; `BUILD_FROM` is added for you |
| `release` | boolean | no (`false`) | Whether to publish the image in a [release](#release-releaseyml) |

#### Templating

`containers.yml` is rendered with [Jinja](https://jinja.palletsprojects.com) before it
is loaded. These functions are available:

| Function | Returns |
| --- | --- |
| `package("<name>")` | The version of `<name>` in `packages.yml` |

Wrap each call in quotes so the result stays a string, e.g.
`"gcc{{ package("gcc-ubuntu24") }}"`.

## Containers

The images come in three layers. Each layer builds on the one before it:

1. **base**: an operating system (optionally with NVIDIA CUDA), basic system packages,
   Python, and [ORAS](https://oras.land) for working with registry artifacts.
2. **compiler**: the base plus a compiler toolchain and Valgrind.
3. **mpi**: the compiler image plus MPI libraries (MPICH and/or OpenMPI) built against
   that compiler.

```mermaid
flowchart LR
    subgraph base
        b_r8[base-rocky8]
        b_r8c[base-rocky8-cuda]
        b_r9[base-rocky9]
        b_u24[base-ubuntu24]
        b_u24c[base-ubuntu24-cuda]
    end
    subgraph compiler
        c_r8g[compiler-rocky8-gcc]
        c_r8cg[compiler-rocky8-cuda-gcc]
        c_r9g[compiler-rocky9-gcc]
        c_u24g[compiler-ubuntu24-gcc]
        c_u24gm[compiler-ubuntu24-gccmin]
        c_u24cl[compiler-ubuntu24-clang]
        c_u24cg[compiler-ubuntu24-cuda-gcc]
    end
    subgraph mpi
        m_r8g[mpi-rocky8-gcc]
        m_r8o[mpi-rocky8-oneapi]
        m_r8cg[mpi-rocky8-cuda-gcc]
        m_r9g[mpi-rocky9-gcc]
        m_u24g[mpi-ubuntu24-gcc]
        m_u24gm[mpi-ubuntu24-gccmin]
        m_u24cl[mpi-ubuntu24-clang]
        m_u24cg[mpi-ubuntu24-cuda-gcc]
    end
    b_r8 --> c_r8g --> m_r8g
    c_r8g --> m_r8o
    b_r8c --> c_r8cg --> m_r8cg
    b_r9 --> c_r9g --> m_r9g
    b_u24 --> c_u24g --> m_u24g
    b_u24 --> c_u24gm --> m_u24gm
    b_u24 --> c_u24cl --> m_u24cl
    b_u24c --> c_u24cg --> m_u24cg
```

Every image is published as `moose-<name>`, for example `moose-mpi-rocky8-gcc`. Exact
versions are in [`packages.yml`](packages.yml).

### Released images

These are the release tags defined by the current `containers.yml`. A new tag is published
once the [Release](#release-releaseyml) workflow runs. This table is generated; don't edit
it by hand.

<!-- releases:start -->
| container                                                                                                                                   | tag                                                             |
|---------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| [`moose-base-rocky8`](https://github.com/idaholab/moose-containers/pkgs/container/moose-containers%2Fmoose-base-rocky8)                     | `8.10-20261008`                                                 |
| [`moose-mpi-rocky8-cuda-gcc`](https://github.com/idaholab/moose-containers/pkgs/container/moose-containers%2Fmoose-mpi-rocky8-cuda-gcc)     | `8.10-cuda13.3.1-gcc13.3.1-mpich5.0.2-openmpi5.0.11-20261008`   |
| [`moose-mpi-rocky8-gcc`](https://github.com/idaholab/moose-containers/pkgs/container/moose-containers%2Fmoose-mpi-rocky8-gcc)               | `8.10-gcc13.3.1-mpich5.0.2-openmpi5.0.11-20261008`              |
| [`moose-mpi-rocky8-oneapi`](https://github.com/idaholab/moose-containers/pkgs/container/moose-containers%2Fmoose-mpi-rocky8-oneapi)         | `8.10-gcc13.3.1-oneapi2026.1.1-mpich4.3.2-20261008`             |
| [`moose-mpi-rocky9-gcc`](https://github.com/idaholab/moose-containers/pkgs/container/moose-containers%2Fmoose-mpi-rocky9-gcc)               | `9.7-gcc13.3.1-mpich4.3.2-openmpi5.0.11-20261008`               |
| [`moose-mpi-ubuntu24-clang`](https://github.com/idaholab/moose-containers/pkgs/container/moose-containers%2Fmoose-mpi-ubuntu24-clang)       | `24.04-clang22.1.8-gcc14.2.0-mpich5.0.2-openmpi5.0.11-20261008` |
| [`moose-mpi-ubuntu24-cuda-gcc`](https://github.com/idaholab/moose-containers/pkgs/container/moose-containers%2Fmoose-mpi-ubuntu24-cuda-gcc) | `24.04-cuda13.3.1-gcc14.2.0-mpich5.0.2-openmpi5.0.11-20261008`  |
| [`moose-mpi-ubuntu24-gcc`](https://github.com/idaholab/moose-containers/pkgs/container/moose-containers%2Fmoose-mpi-ubuntu24-gcc)           | `24.04-gcc14.2.0-mpich5.0.2-openmpi5.0.11-20261008`             |
| [`moose-mpi-ubuntu24-gccmin`](https://github.com/idaholab/moose-containers/pkgs/container/moose-containers%2Fmoose-mpi-ubuntu24-gccmin)     | `24.04-gcc9.5.0-mpich5.0.2-20261008`                            |
<!-- releases:end -->

### Base images

| Container | Description |
|---|---|
| `moose-base-rocky8` | Rocky Linux 8, plus [Apptainer](https://apptainer.org) |
| `moose-base-rocky8-cuda` | Rocky Linux 8 with the NVIDIA CUDA toolkit and NCCL |
| `moose-base-rocky9` | Rocky Linux 9 |
| `moose-base-ubuntu24` | Ubuntu 24.04 |
| `moose-base-ubuntu24-cuda` | Ubuntu 24.04 with the NVIDIA CUDA toolkit |

### Compiler images

| Container | Description |
|---|---|
| `moose-compiler-rocky8-gcc` | GCC (gcc-toolset) on Rocky Linux 8 |
| `moose-compiler-rocky8-cuda-gcc` | GCC (gcc-toolset) on Rocky Linux 8 with CUDA |
| `moose-compiler-rocky9-gcc` | GCC (gcc-toolset) on Rocky Linux 9 |
| `moose-compiler-ubuntu24-gcc` | A recent GCC on Ubuntu 24.04 |
| `moose-compiler-ubuntu24-gccmin` | The oldest GCC that MOOSE supports, on Ubuntu 24.04 |
| `moose-compiler-ubuntu24-clang` | LLVM Clang on Ubuntu 24.04, with GCC's gfortran for Fortran |
| `moose-compiler-ubuntu24-cuda-gcc` | GCC on Ubuntu 24.04 with CUDA |

### MPI images

| Container | Description |
|---|---|
| `moose-mpi-rocky8-gcc` | MPICH and OpenMPI built with GCC on Rocky Linux 8 |
| `moose-mpi-rocky8-oneapi` | Intel oneAPI compilers, with MPICH built using them, on Rocky Linux 8 |
| `moose-mpi-rocky8-cuda-gcc` | MPICH (with UCX) and OpenMPI built with GCC on Rocky Linux 8 with CUDA |
| `moose-mpi-rocky9-gcc` | MPICH and OpenMPI built with GCC on Rocky Linux 9 |
| `moose-mpi-ubuntu24-gcc` | MPICH and OpenMPI built with GCC on Ubuntu 24.04 |
| `moose-mpi-ubuntu24-gccmin` | MPICH built with the minimum supported GCC on Ubuntu 24.04 |
| `moose-mpi-ubuntu24-clang` | MPICH and OpenMPI built with Clang on Ubuntu 24.04 |
| `moose-mpi-ubuntu24-cuda-gcc` | MPICH and OpenMPI built with GCC on Ubuntu 24.04 with CUDA |

### Using an image

Every image includes a `/moose_env.sh` script. Each layer adds to it to set up the
environment that layer provides: the compiler on `PATH`, `CC`/`CXX`/`FC`, CUDA, and the
locations of the MPI installs (`MOOSE_MPICH_DIR`, `MOOSE_OPENMPI_DIR`). Source it before
building:

```bash
source /moose_env.sh
```

## From pull request to release

Images go through three stages. Images from the first two stages go to `staging-`
repositories in the registry, so test images never mix with released ones.

| Stage | When | Where the image goes |
|---|---|---|
| **Pull request** | A pull request against `main` is opened or updated | `staging-moose-<name>:pr<N>-<tag>` |
| **Main** | A pull request is merged into `main` | `staging-moose-<name>:main-<tag>` and `:latest` |
| **Release** | A maintainer runs the **Release** workflow | `moose-<name>:<tag>` |

### Pull requests ([`build.yml`](.github/workflows/build.yml))

Changed containers are built in dependency order; unchanged parents are reused from
`main`. The workflow posts a comment on the pull request summarizing:

- which containers will be built, with their old and new tags,
- which package versions changed, and
- which release containers have not been released yet.

At the end, the workflow checks that every container in `containers.yml` exists in the
registry for this pull request or on `main`.

The build cache is kept between runs of the same pull request. To clear it, add the
`ci: delete cache` label to the pull request.

#### Pull requests from forks

A pull request from a fork gets a read-only token, so it can't push images or comment.
It runs in two parts:

1. `ruff`, `pytest`, and `generated` run as usual, once GitHub's
   [approval for outside contributors](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/approve-runs-from-forks)
   allows them.
2. The build waits on the `fork-pr` job, which needs a maintainer's approval through
   the `fork-pr` environment. Review the changes first, Dockerfiles and helper scripts
   included, and then choose **Review deployments** on the run. Each push to the pull
   request needs a new approval.

The approved run uses `main`'s workflow, tooling, and build action. It takes only the
pull request's `containers.yml`, `packages.yml`, and Docker contexts, and only from the
commit that was approved. Changes a fork makes to `.github` or `moosecontainers` are
tested in part 1 but aren't used to build. A fork can't contain symlinks. Its
configuration values may only use characters that are safe in tags, paths, and build
arguments.

GitHub blocks `pull_request_target` in public repositories unless an Actions policy
allows it. The repository's policy is kept in
[`.github/policies/pull-request-target.json`](.github/policies/pull-request-target.json),
and only allows it for `build.yml` and `delete-images.yml`. It's a repository setting,
so editing the file changes nothing on its own; apply it with:

```bash
gh api -X PUT repos/idaholab/moose-containers/actions/policies/<id> \
  --input .github/policies/pull-request-target.json
```

where `<id>` is from `gh api repos/idaholab/moose-containers/actions/policies`.

### Main ([`build.yml`](.github/workflows/build.yml))

After a merge, the changed containers are rebuilt and tagged as `main`. These are the
images that release candidates are taken from. If a container's tag didn't change but its
`main` image is missing from the registry, it is rebuilt.

### Release ([`release.yml`](.github/workflows/release.yml))

Releasing is a manual step. A maintainer starts the **Release** workflow from `main`.
By default it runs as a **dry run**, which only reports what would be released. When it
runs for real (this requires approval through the `release` environment), it:

1. merges `main` into the `release` branch, and
2. for each container marked [`release: true`](#containersyml) that hasn't been released
   at its current tag, copies the existing `main` image to the release location. The
   image is promoted as it is, not rebuilt.

Only the images MOOSE actually uses are marked for release: `moose-base-rocky8` and every
`moose-mpi-*` image. The base and compiler images in between exist to build those.

## Cleanup

The **[Delete images](.github/workflows/delete-images.yml)** workflow keeps the staging
registry from filling up:

- It runs automatically when a pull request is closed, and deletes that pull request's
  images and build cache.
- It can also be run by hand. Choose `all-prs` to delete the images from every pull
  request, or `untagged` to delete untagged image versions left behind in the staging
  repositories. Check **dry_run** to only list what would be deleted.

## CI tooling

The workflows run the [`moosecontainers`](moosecontainers) Python package, which works
out what to build, release, and delete, and generates `build.yml` and the release table.
Run it with `uv run moosecontainers <action>`; `uv run moosecontainers --help` lists the
actions. Its tests are in [`tests`](tests) and run with:

```bash
uv run pytest
```

The tests mock every request to GitHub and require 100% coverage.

The build workflow, [`build.yml`](.github/workflows/build.yml), has one job per
container, so each container waits only for its own parent. It is generated from
[`.github/templates/build.yml.j2`](.github/templates/build.yml.j2) and `containers.yml`.
After adding, removing or re-parenting a container, regenerate it with
`uv run moosecontainers workflows`. The pull request build fails if it is out of date.
