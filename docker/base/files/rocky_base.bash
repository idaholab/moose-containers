#!/bin/bash

#
# Performs updates for the base rocky image and
# installs the base reqirements
#
#

set -eux

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <rocky version>" >&2
  exit 1
fi

ROCKY_VERSION="$1"

# Make sure version is the version expected
source /etc/os-release && [ "$VERSION_ID" == "$ROCKY_VERSION" ]

# Update
dnf upgrade -y

# Install basic packages
dnf install -y bzip2 git git-lfs tar vim wget rsync hostname jq \
    diffutils file unzip findutils procps-ng xz file which time

# Cleanup
dnf clean all
