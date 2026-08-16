#
# moose-base-rocky8-cuda
#
# Required build arguments:
#
#   CONTAINER_NAME: Name for the container
#   CUDA_VERSION: Version of CUDA
#   ORAS_VERSION: Version of oras
#   ROCKY_VERSION: Version of rocky8
#

ARG CUDA_VERSION=unset
FROM nvidia/cuda:${CUDA_VERSION}-devel-rockylinux8

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

# Install nccl, which was included previously in 12.9 but
# as of 13.1 it looks like it's not
RUN dnf install -y libnccl libnccl-devel libnccl-static && \
    dnf clean all

# Add to environment
ARG CONTAINER_NAME
ARG MOOSE_ENV=/moose_env.sh
RUN test -n "$CONTAINER_NAME" && \
    test -d /usr/local/cuda && \
    echo "#!/bin/sh" >> ${MOOSE_ENV} && \
    echo "# From ${CONTAINER_NAME}" >> ${MOOSE_ENV} && \
    echo "export CUDA_DIR=/usr/local/cuda" >> ${MOOSE_ENV} && \
    chmod +x ${MOOSE_ENV}
