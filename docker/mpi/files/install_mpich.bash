#!/bin/bash

#
# Builds and installs mpich
#

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <version> <install dir> <configure arguments...>" >&2
  exit 1
fi

set -eux
set -o pipefail

MPICH_VERSION="$1"
MPICH_DIR="$2"
CONFIGURE_ARGS=("${@:3}")
BUILD_JOBS="${BUILD_JOBS:-4}"

BUILD_DIR=/root/build
mkdir "$BUILD_DIR"
cd "$BUILD_DIR"

MPICH_NAME="mpich-${MPICH_VERSION}"
MPICH_URL="https://github.com/pmodels/mpich/releases/download/v${MPICH_VERSION}/mpich-${MPICH_VERSION}.tar.gz"
MPICH_TAR="${BUILD_DIR}/mpich.tar.gz"

if [ -n "${CUDA_DIR:-}" ]; then
  CONFIGURE_ARGS=("--with-cuda=${CUDA_DIR}" "${CONFIGURE_ARGS[@]}")
fi

mkdir -p "${MPICH_DIR}/logs"
curl -L "$MPICH_URL" -o "$MPICH_TAR"
tar xf "$MPICH_TAR" -C "$BUILD_DIR"
rm "$MPICH_TAR"
cd "${BUILD_DIR}/${MPICH_NAME}"
mkdir build
cd build
../configure \
    --prefix="$MPICH_DIR" \
    "${CONFIGURE_ARGS[@]}" | tee "${MPICH_DIR}/logs/configure.log"
make -j "$BUILD_JOBS" 2>&1 | tee "${MPICH_DIR}/logs/build.log"
make install 2>&1 | tee "${MPICH_DIR}/logs/install.log"
rm -rf "$BUILD_DIR"

ENV_SCRIPT="${MPICH_DIR}/env.sh"
cat <<EOF >> "$ENV_SCRIPT"
export LD_LIBRARY_PATH=${MPICH_DIR}/lib:\${LD_LIBRARY_PATH:-}
export MANPATH=${MPICH_DIR}/share/man:\${MANPATH:-}
export PATH=${MPICH_DIR}/bin:\${PATH:-}
export CC=mpicc CXX=mpicxx FC=mpif90 F90=mpif90 F77=mpif77
EOF

set +u
source "$ENV_SCRIPT"
if [ -n "$CUDA_DIR" ]; then
  export LD_LIBRARY_PATH="${CUDA_DIR}/compat:${LD_LIBRARY_PATH}"
fi
mpiexec --version
