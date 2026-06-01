#
# moose-mpi-rocky8-gccmin
#
# Required build arguments:
#
#   BUILD_FROM: FROM image
#   GCC_VERSION: Version of gcc
#   MPICH_VERSION: Version of mpich
#   URI: URI for the built image
#

ARG BUILD_FROM=unset
FROM $BUILD_FROM

# Install GCC
ARG GCC_VERSION
RUN test -n "$GCC_VERSION" && \
    GCC_MAJOR_VERSION="$(echo "$GCC_VERSION" | cut -d'.' -f1)" && \
    dnf install -y gcc-toolset-${GCC_MAJOR_VERSION} && \
    dnf clean all && \
    . "/opt/rh/gcc-toolset-${GCC_MAJOR_VERSION}/enable" && \
    gcc --version | grep -q "(GCC) ${GCC_VERSION} "

# Path to the moose env script
ARG MOOSE_ENV=/moose_env.sh
# Number of jobs to build with
ARG BUILD_JOBS=4

# Install mpich
ARG MPICH_DIR=/opt/mpich
ARG MPICH_VERSION
COPY files/install_mpich.bash /root/install_mpich.bash
RUN . "$MOOSE_ENV" && \
    GCC_MAJOR_VERSION="$(echo "$GCC_VERSION" | cut -d'.' -f1)" && \
    . "/opt/rh/gcc-toolset-${GCC_MAJOR_VERSION}/enable" && \
    /bin/bash /root/install_mpich.bash "$MPICH_VERSION" "$MPICH_DIR" --enable-mpi-api && \
    rm /root/install_mpich.bash

# Expose GCC and MPI
ARG URI
RUN test -f ${MOOSE_ENV} && \
    GCC_MAJOR_VERSION="$(echo "$GCC_VERSION" | cut -d'.' -f1)" && \
    echo "# From ${URI}" >> ${MOOSE_ENV} && \
    echo ". /opt/rh/gcc-toolset-${GCC_MAJOR_VERSION}/enable" >> ${MOOSE_ENV} && \
    echo "export MOOSE_MPICH_DIR=${MPICH_DIR}" >> ${MOOSE_ENV}
