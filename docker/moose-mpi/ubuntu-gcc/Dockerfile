#
# Used for:
#
#   moose-mpi-ubuntu24-cuda-gcc
#   moose-mpi-ubuntu24-gcc
#
# Required build arguments:
#
#   BUILD_FROM: FROM image
#   MPICH_VERSION: Version of mpich
#   OPENMPI_VERSION: Version of openmpi
#   URI: URI for the built image
#

ARG BUILD_FROM=unset
FROM $BUILD_FROM

# Path to the moose env script
ARG MOOSE_ENV=/moose_env.sh
# Number of jobs to build with
ARG BUILD_JOBS=4

# Install mpich
ARG MPICH_DIR=/opt/mpich
ARG MPICH_VERSION
COPY files/install_mpich.bash /root/install_mpich.bash
RUN . "$MOOSE_ENV" && \
    /bin/bash /root/install_mpich.bash "$MPICH_VERSION" "$MPICH_DIR" --enable-mpi-api && \
    rm /root/install_mpich.bash

# Install openmpi
ARG OPENMPI_DIR=/opt/openmpi
ARG OPENMPI_VERSION
COPY files/install_openmpi.bash /root/install_openmpi.bash
RUN . "$MOOSE_ENV" && \
    /bin/bash /root/install_openmpi.bash "$OPENMPI_VERSION" "$OPENMPI_DIR" && \
    rm /root/install_openmpi.bash

# Expose MPI directories as env vars
ARG URI
RUN test -f ${MOOSE_ENV} && \
    echo "# From ${URI}" >> ${MOOSE_ENV} && \
    echo "export MOOSE_MPICH_DIR=${MPICH_DIR}" >> ${MOOSE_ENV} && \
    echo "export MOOSE_OPENMPI_DIR=${OPENMPI_DIR}" >> ${MOOSE_ENV}
