#
# Used for:
#
#   moose-mpi-rocky8-gcc
#   moose-mpi-rocky8-cuda-gcc
#   moose-mpi-rocky9-gcc
#
# Required build arguments:
#
#   BUILD_FROM: FROM image
#   CONTAINER_NAME: Name for the container
#   MPICH_VERSION: Version of mpich
#   OPENMPI_VERSION: Version of openmpi
#
# Optional build arguments:
#
#  BUILD_JOBS: Number of jobs to use during a build
#  MPICH_ARGS: Extra arguments to pass to the MPICH configure
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
ARG MPICH_ARGS
RUN --mount=type=bind,source=files/install_mpich.bash,target=/root/install_mpich.bash \
    . "$MOOSE_ENV" && \
    eval "/bin/bash /root/install_mpich.bash \"$MPICH_VERSION\" \"$MPICH_DIR\" --enable-mpi-api $MPICH_ARGS"

# Install openmpi
ARG OPENMPI_DIR=/opt/openmpi
ARG OPENMPI_VERSION
COPY files/install_openmpi.bash /root/install_openmpi.bash
RUN --mount=type=bind,source=files/install_openmpi.bash,target=/root/install_openmpi.bash \
    . "$MOOSE_ENV" && \
    /bin/bash /root/install_openmpi.bash "$OPENMPI_VERSION" "$OPENMPI_DIR"

# Expose MPI directories as env vars
ARG CONTAINER_NAME
RUN test -f ${MOOSE_ENV} && \
    echo "# From ${CONTAINER_NAME}" >> ${MOOSE_ENV} && \
    echo "export MOOSE_MPICH_DIR=${MPICH_DIR}" >> ${MOOSE_ENV} && \
    echo "export MOOSE_OPENMPI_DIR=${OPENMPI_DIR}" >> ${MOOSE_ENV}
