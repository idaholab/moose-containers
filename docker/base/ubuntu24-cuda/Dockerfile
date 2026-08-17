#
# moose-base-ubuntu24-cuda
#
# Required build arguments:
#
#   CONTAINER_NAME: Name for the container
#   CUDA_VERSION: Version of CUDA
#   UBUNTU_VERSION: Version of ubuntu
#   ORAS_VERSION: Version of oras
#

ARG CUDA_VERSION=unset
ARG UBUNTU_VERSION=unset
FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION}

# Update, install basic packages + python
COPY files/ubuntu_base.bash /root/ubuntu_base.bash
RUN /bin/bash /root/ubuntu_base.bash && rm /root/ubuntu_base.bash

# Install ORAS
COPY files/install_oras.bash /root/install_oras.bash
ARG ORAS_VERSION
RUN /bin/bash /root/install_oras.bash "$ORAS_VERSION" /usr/local/bin && rm /root/install_oras.bash

# Add to environment
ARG CONTAINER_NAME
ARG MOOSE_ENV=/moose_env.sh
RUN test -n "$CONTAINER_NAME" && \
    test -d /usr/local/cuda && \
    echo "# From ${CONTAINER_NAME}" >> ${MOOSE_ENV} && \
    echo "export CUDA_DIR=/usr/local/cuda" >> ${MOOSE_ENV} && \
    chmod +x ${MOOSE_ENV}
