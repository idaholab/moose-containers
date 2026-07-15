#
# moose-base-rocky8
#
# Required build arguments:
#
#   CONTAINER_NAME: Name for the container
#   ORAS_VERSION: Version of oras
#   ROCKY_VERSION: Version of rocky8
#

FROM rockylinux/rockylinux:8.10.20240528

# Install ORAS
COPY files/install_oras.bash /root/install_oras.bash
ARG ORAS_VERSION
RUN /bin/bash /root/install_oras.bash "$ORAS_VERSION" /usr/local/bin && rm /root/install_oras.bash

# Test version, upgrade, install basic packages
COPY files/rocky_base.bash /root/rocky_base.bash
ARG ROCKY_VERSION
RUN /bin/bash /root/rocky_base.bash "$ROCKY_VERSION" && rm /root/rocky_base.bash

# Install python
COPY files/rocky8_python.bash /root/rocky8_python.bash
RUN /bin/bash /root/rocky8_python.bash && rm /root/rocky8_python.bash

# Install apptainer
RUN dnf -y install epel-release && \
    dnf -y install apptainer && \
    dnf clean all

# Add to environment
ARG CONTAINER_NAME
ARG MOOSE_ENV=/moose_env.sh
RUN test -n "$CONTAINER_NAME" && \
    echo "# From ${CONTAINER_NAME}" >> ${MOOSE_ENV} && \
    chmod +x ${MOOSE_ENV}
