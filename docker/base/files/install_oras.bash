#!/bin/bash

#
# Installs oras
#

set -eux

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <oras version> <installation directory>" >&2
  exit 1
fi

ORAS_VERSION="$1"
INSTALL_DIR="$2"

BUILD_DIR=/root/build
ORAS_TAR="${BUILD_DIR}/oras.tar.gz"
ORAS_DIR="${BUILD_DIR}/oras"
ORAS_URL="https://github.com/oras-project/oras/releases/download/v${ORAS_VERSION}/oras_${ORAS_VERSION}_linux_amd64.tar.gz"

mkdir "$BUILD_DIR"
cd "$BUILD_DIR"
curl -L "$ORAS_URL" -o "$ORAS_TAR"
mkdir "$ORAS_DIR"
tar -zxf "$ORAS_TAR" -C "$ORAS_DIR"
rm "$ORAS_TAR"
mv "${ORAS_DIR}/oras" "${INSTALL_DIR}/"
rm -rf "$BUILD_DIR"
