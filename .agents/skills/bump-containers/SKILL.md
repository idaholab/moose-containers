---
name: bump-containers
description: Rebuild every moose-containers image by bumping all container dates in containers.yml to today and updating dependency versions in packages.yml (plus the pinned Rocky FROM lines and VALGRIND_VERSION), then regenerate the README, check locally and open a PR. Use when asked to bump, refresh, or update all containers or their packages.
---

# Bump all containers

The model is idaholab/moose-containers#57 ("Bump all containers, update mpich")
and #45 ("Update all containers"). A routine bump changes only `containers.yml`,
`packages.yml` and `README.md`, plus a Dockerfile when a version lives there
(see step 3). Read `AGENTS.md` first; its rules apply here.

Invoking this skill is permission to run the git commands in steps 1 and 7 in
this repo. Ask before running any other git commands.

## 1. Branch from the latest main

- `git fetch origin`, then `git switch -c update_$(date +%Y%m) origin/main`
  (#57 used `update_202610`). If the working tree is dirty or the branch
  already exists, stop and ask.

## 2. Find newer versions

Check each entry in `packages.yml` against upstream. Commands that work:

| package | where to look |
|---|---|
| `mpich` | `gh api repos/pmodels/mpich/releases --jq '[.[]\|select(.prerelease\|not)\|.tag_name][:5]'` |
| `openmpi` | `gh api 'repos/open-mpi/ompi/tags?per_page=30' --jq '[.[].name\|select(test("^v[0-9.]+$"))][:5]'` (it has no GitHub releases) |
| `oras` | `gh api repos/oras-project/oras/releases --jq '[.[]\|select(.prerelease\|not)\|.tag_name][:5]'` |
| `cuda` | Docker Hub tags for `nvidia/cuda`, filtered by `devel-rockylinux8` and `devel-ubuntu24.04`. Both must exist (see below). |
| `rocky8`/`rocky9` | Docker Hub tags for `rockylinux/rockylinux`. Use the dated tags (e.g. `9.8.20260525.0`). |
| `oneapi` | `version="..."` of `intel-oneapi-compiler-dpcpp-cpp` in the primary.xml.gz listed in `https://yum.repos.intel.com/oneapi/repodata/repomd.xml` |
| `gcc-rocky8`/`gcc-rocky9` | Newest `gcc-toolset-<major>-gcc-*.rpm` in `https://dl.rockylinux.org/pub/rocky/<8\|9>/AppStream/x86_64/os/Packages/g/` |
| `gcc-ubuntu24*`, `gcc-min-ubuntu24` | Launchpad `getPublishedSources` for `gcc-<major>` in `noble`. The version is the upstream part (`14.2.0` from `14.2.0-4ubuntu2~24.04.1`). |
| `clang-ubuntu24` | `Version:` of `clang-<major>` in `https://apt.llvm.org/noble/dists/llvm-toolchain-noble-<major>/main/binary-amd64/Packages.gz` |
| `VALGRIND_VERSION` | `https://sourceware.org/pub/valgrind/` |

Docker Hub tags:

```bash
curl -s "https://hub.docker.com/v2/repositories/<namespace>/<repo>/tags?page_size=25&name=<filter>&ordering=last_updated" \
  | python3 -c 'import sys,json;print([t["name"] for t in json.load(sys.stdin)["results"]])'
```

Put downloaded files (e.g. the oneAPI primary.xml.gz) in a fresh `mktemp -d`.

### What to change without asking, and what to ask about

The compiler and package tags must match what the distribution actually
installs. The Dockerfiles `grep` the installed version and fail if it differs.

- **Update without asking:** patch and minor releases of `mpich`, `openmpi`,
  `oras`, `oneapi`, and of `VALGRIND_VERSION`. Also a newer patch of
  `gcc-rocky*`, `gcc-ubuntu24*` or `clang-ubuntu24` within the same major, but
  only when the distro or apt.llvm.org package is that version.
- **Ask first:**
  - Major releases of anything.
  - A new compiler major (gcc-toolset-15, clang-23). That changes which
    packages get installed.
  - `cuda` minor versions. There must be a `<ver>-devel-rockylinux8` and a
    `<ver>-devel-ubuntu24.04` tag.
  - Rocky point releases (`9.7` → `9.8`).
- **Leave alone unless asked:**
  - `ubuntu24`. A new Ubuntu release means new containers.
  - The "alternate versions" (`mpich-rocky8-oneapi`, `mpich-rocky9`). They are
    deliberately held back. #23 reverted an mpich update on oneapi because PETSc
    failed. Report newer versions of them, but don't change them.

Show the user a table of current → latest versions, marked with what you plan
to change, and wait for confirmation.

## 3. Apply the version changes

- Edit `packages.yml`. Only the quoted value changes, e.g. `mpich: "5.0.2"`.
- If `rocky8`/`rocky9` changes, also update the pinned
  `FROM rockylinux/rockylinux:<dated tag>` in `docker/base/rocky8/Dockerfile` or
  `docker/base/rocky9/Dockerfile`. Use the same version, or the build fails. For
  rocky8, check that the new `FROM` tag is newer than the current pin.
- If valgrind changes, update `ARG VALGRIND_VERSION=` in **all** of
  `docker/compiler/*/Dockerfile` (rocky-gcc, ubuntu-gcc, ubuntu-clang).
  `grep -rn VALGRIND_VERSION= docker` lists them.

## 4. Bump every container date

Set every `date:` in `containers.yml` to today (`date +%Y%m%d`). All
containers get the same date, including those that don't use a changed
package. That is what makes the whole tree rebuild. The date must not be in
the future, and must not be earlier than the current one.

```bash
sed -i '' -E "s/^(  date: )\"[0-9]{8}\"/\1\"$(date +%Y%m%d)\"/" containers.yml
```

Check that the number of changed lines equals the number of containers.

## 5. Regenerate and update the README

- `uv run moosecontainers readme` regenerates the "Released images" table.
- `uv run moosecontainers workflows` should leave `build.yml` unchanged after a
  bump. If it changes, include that.
- The example tag in README "Versioning" is written by hand
  (`moose-mpi-ubuntu24-gcc:<ubuntu>-gcc<ver>-mpich<ver>-openmpi<ver>-<date>`).
  Update it to the new tag. #57 forgot to, so it may already be stale.

## 6. Check locally

- `uv run moosecontainers prepare_push origin/main`. Every container should
  be listed as building, with the new tags. The changed packages should match
  what you changed.
- `git diff --stat` should only list the expected files.
- Run `uv run pytest` and `uvx --from actionlint-py actionlint` only if
  something other than YAML and README changed.

## 7. Commit, push, open the PR

- One commit with a title in the style of #57, e.g. `Bump all containers,
  update mpich and oras`, or `Bump all containers` if no versions changed.
- `git push -u origin <branch>`, then `gh pr create --base main` with the same
  title and a body that lists the changes, like #57:

  ```
  - Update mpich to 5.0.2
  - Update oras to 1.3.6
  - Bump all container dates
  ```

- Report the PR URL, the versions that changed, and the newer versions you
  skipped (with the reason for each).
