#!/bin/bash

#
# Updates and installs the base packages
# and python for ubuntu containers
#

set -eux

if [ "$#" -ne 0 ]; then
  echo "Usage: $0" >&2
  exit 1
fi

PYTHON_VERSION="3.12"

# Update and upgrade
apt-get update
apt-get upgrade -y
apt-get dist-upgrade -y

# Install base packages and python
apt-get install -y --no-install-recommends \
  bzip2 git git-lfs tar vim wget rsync hostname jq diffutils file unzip \
  findutils procps xz-utils file which time curl ca-certificates zlib1g-dev \
  python3 python3-yaml python3-jinja2 curl pkgconf gdb

# Check python version
which python${PYTHON_VERSION}

# Use new python as default
update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 100
python --version | grep ${PYTHON_VERSION}

# Cleanup
apt-get autoremove -y
apt-get clean
rm -rf /var/lib/apt/lists/*
