#!/bin/bash

#
# Builds and installs openmpi
#

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <version> <install dir> <configure arguments...>" >&2
  exit 1
fi

set -eux
set -o pipefail

OPENMPI_VERSION="$1"
OPENMPI_DIR="$2"
CONFIGURE_ARGS=("${@:3}")
BUILD_JOBS="${BUILD_JOBS:-4}"

BUILD_DIR=/root/build
mkdir "$BUILD_DIR"
cd "$BUILD_DIR"

OPENMPI_MAJOR_VERSION="$(cut -d '.' -f 1,2 <<< "${OPENMPI_VERSION}")"
OPENMPI_NAME="openmpi-${OPENMPI_VERSION}"
OPENMPI_URL="https://download.open-mpi.org/release/open-mpi/v${OPENMPI_MAJOR_VERSION}/${OPENMPI_NAME}.tar.gz"
OPENMPI_TAR="${BUILD_DIR}/openmpi.tar.gz"

if [ -n "${CUDA_DIR:-}" ]; then
  CONFIGURE_ARGS=("--with-cuda=${CUDA_DIR}" "${CONFIGURE_ARGS[@]}")
fi

mkdir -p "${OPENMPI_DIR}/logs"
curl -L "$OPENMPI_URL" -o "$OPENMPI_TAR"
tar xf "$OPENMPI_TAR" -C "$BUILD_DIR"
rm "$OPENMPI_TAR"
cd "${BUILD_DIR}/${OPENMPI_NAME}"
mkdir build
cd build
../configure \
    --prefix="$OPENMPI_DIR" \
    "${CONFIGURE_ARGS[@]}" | tee "${OPENMPI_DIR}/logs/configure.log"
make -j "$BUILD_JOBS" 2>&1 | tee "${OPENMPI_DIR}/logs/build.log"
make install 2>&1 | tee "${OPENMPI_DIR}/logs/install.log"
rm -rf "$BUILD_DIR"

ENV_SCRIPT="${OPENMPI_DIR}/env.sh"
cat <<EOF >> "$ENV_SCRIPT"
export LD_LIBRARY_PATH=${OPENMPI_DIR}/lib:\${LD_LIBRARY_PATH}
export MANPATH=${OPENMPI_DIR}/share/man:\${MANPATH}
export PATH=${OPENMPI_DIR}/bin:\${PATH}
export CC=mpicc CXX=mpicxx FC=mpif90 F90=mpif90 F77=mpif77
EOF

set +u
source "$ENV_SCRIPT"
mpiexec --version
ompi_info
