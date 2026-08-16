#!/bin/bash

#
# Builds and installs valgrind
#

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <version> <install dir> <configure arguments...>" >&2
  exit 1
fi

set -eux
set -o pipefail

VALGRIND_VERSION="$1"
VALGRIND_DIR="$2"
CONFIGURE_ARGS=("${@:3}")
BUILD_JOBS="${BUILD_JOBS:-4}"

BUILD_DIR=/root/build
mkdir "$BUILD_DIR"
cd "$BUILD_DIR"

VALGRIND_NAME="valgrind-${VALGRIND_VERSION}"
VALGRIND_URL="https://sourceware.org/pub/valgrind/${VALGRIND_NAME}.tar.bz2"
VALGRIND_TAR="${BUILD_DIR}/valgrind.tar.bz2"

mkdir -p "${VALGRIND_DIR}/logs"
curl -L "$VALGRIND_URL" -o "$VALGRIND_TAR"
tar xf "$VALGRIND_TAR" -C "$BUILD_DIR"
rm "$VALGRIND_TAR"
cd "${BUILD_DIR}/${VALGRIND_NAME}"
mkdir build
cd build
../configure \
    --prefix="$VALGRIND_DIR" \
    "${CONFIGURE_ARGS[@]}" | tee "${VALGRIND_DIR}/logs/configure.log"
make -j "$BUILD_JOBS" 2>&1 | tee "${VALGRIND_DIR}/logs/build.log"
make install 2>&1 | tee "${VALGRIND_DIR}/logs/install.log"
rm -rf "$BUILD_DIR"
