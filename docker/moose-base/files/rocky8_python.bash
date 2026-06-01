#!/bin/bash

#
# Installs the base python for rocky8 containers
#

set -eux

if [ "$#" -ne 0 ]; then
  echo "Usage: $0" >&2
  exit 1
fi

PYTHON_VERSION="3.12"

# Install python
dnf install -y "python${PYTHON_VERSION}" "python${PYTHON_VERSION}-devel" \
    "python${PYTHON_VERSION}-pip" "python${PYTHON_VERSION}-setuptools"
alternatives --set python "/usr/bin/python${PYTHON_VERSION}"
alternatives --set python3 "/usr/bin/python${PYTHON_VERSION}"
"pip${PYTHON_VERSION}" install --no-cache pyyaml jinja2

# Cleanup
dnf clean all
