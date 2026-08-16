#
# Used for:
#
#   moose-mpi-ubuntu24-cuda-gcc
#   moose-mpi-ubuntu24-gcc
#
# Required build arguments:
#
#   BUILD_FROM: FROM image
#   CONTAINER_NAME: Name for the container
#
# Optional build arguments:
#
#   MPICH_VERSION: Version of mpich to install, if it should be installed
#   OPENMPI_VERSION: Version of openmpi to install, if it should be installed
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
RUN --mount=type=bind,source=files/install_mpich.bash,target=/root/install_mpich.bash \
    if [ -n "$MPICH_VERSION" ]; then \
        . "$MOOSE_ENV" && \
        /bin/bash /root/install_mpich.bash "$MPICH_VERSION" "$MPICH_DIR" --enable-mpi-api; \
    fi

# Install openmpi
ARG OPENMPI_DIR=/opt/openmpi
ARG OPENMPI_VERSION
RUN --mount=type=bind,source=files/install_openmpi.bash,target=/root/install_openmpi.bash \
    if [ -n "$OPENMPI_VERSION" ]; then \
        . "$MOOSE_ENV" && \
        /bin/bash /root/install_openmpi.bash "$OPENMPI_VERSION" "$OPENMPI_DIR"; \
    fi

# Expose MPI directories as env vars
ARG CONTAINER_NAME
RUN test -f ${MOOSE_ENV} && \
    test -n "$CONTAINER_NAME" && \
    echo "# From ${CONTAINER_NAME}" >> ${MOOSE_ENV} && \
    if [ -n "$MPICH_VERSION" ]; then \
        echo "export MOOSE_MPICH_DIR=${MPICH_DIR}" >> ${MOOSE_ENV}; \
    fi && \
    if [ -n "$OPENMPI_VERSION" ]; then \
        echo "export MOOSE_OPENMPI_DIR=${OPENMPI_DIR}" >> ${MOOSE_ENV}; \
    fi;
