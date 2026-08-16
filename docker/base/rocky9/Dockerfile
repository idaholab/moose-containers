#
# moose-base-rocky9
#
# Required build arguments:
#
#   CONTAINER_NAME: Name for the container
#   ROCKY_VERSION: Version of rocky9
#   ORAS_VERSION: Version of oras
#

FROM rockylinux/rockylinux:9.7.20251123

# Install ORAS
COPY files/install_oras.bash /root/install_oras.bash
ARG ORAS_VERSION
RUN /bin/bash /root/install_oras.bash "$ORAS_VERSION" /usr/local/bin && rm /root/install_oras.bash

# Test version, upgrade, install basic packages
COPY files/rocky_base.bash /root/rocky_base.bash
ARG ROCKY_VERSION
RUN /bin/bash /root/rocky_base.bash "$ROCKY_VERSION" && rm /root/rocky_base.bash

# Install python
RUN dnf install -y python python-devel python-pip python-setuptools && \
    pip3 install pyyaml jinja2 && \
    dnf clean all

# Add to environment
ARG CONTAINER_NAME
ARG MOOSE_ENV=/moose_env.sh
RUN test -n "$CONTAINER_NAME" && \
    echo "# From ${CONTAINER_NAME}" >> ${MOOSE_ENV} && \
    chmod +x ${MOOSE_ENV}
