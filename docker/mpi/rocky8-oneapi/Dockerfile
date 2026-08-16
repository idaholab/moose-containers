#
# moose-mpi-rocky8-oneapi
#
# Required build arguments:
#
#   BUILD_FROM: FROM image
#   CONTAINER_NAME: Name for the container
#   ONEAPI_VERSION: Version of Intel oneapi
#   MPICH_VERSION: Version of mpich
#   URI: URI for the built image
#

ARG BUILD_FROM=unset
FROM $BUILD_FROM

# Install intel oneapi
COPY rocky8-oneapi/files/oneAPI.repo /etc/yum.repos.d/oneAPI.repo
RUN dnf install -y intel-oneapi-compiler-dpcpp-cpp intel-oneapi-openmp intel-oneapi-compiler-fortran && \
    dnf clean all

# Store the variables we need from the "setvars.sh" script and add to environment
ARG ONEAPI_SETVARS=/opt/intel/oneapi/moose_setvars.sh
RUN --mount=type=bind,source=rocky8-oneapi/files/setup_vars.bash,target=/root/setup_vars.bash \
    /bin/bash /root/setup_vars.bash "$ONEAPI_SETVARS"

# Check oneapi version
ARG ONEAPI_VERSION
RUN . "$ONEAPI_SETVARS" && \
    icx --version && \
    icx --version | grep -q "Compiler $ONEAPI_VERSION "

# Path to the moose env script
ARG MOOSE_ENV=/moose_env.sh

# Number of jobs to build with
ARG BUILD_JOBS=4

# Install mpich
ARG MPICH_DIR=/opt/mpich
ARG MPICH_VERSION
RUN --mount=type=bind,source=files/install_mpich.bash,target=/root/install_mpich.bash \
    . "$MOOSE_ENV" && \
    . "$ONEAPI_SETVARS" && \
    /bin/bash /root/install_mpich.bash \
        "$MPICH_VERSION" \
        "$MPICH_DIR" \
        CC=icx \
        CXX=icpx \
        FC=ifx \
        F77=ifx \
        F90=ifx \
        --with-device=ch3:nemesis

# Expose oneapi and MPI directory as env vars
ARG CONTAINER_NAME
RUN test -f ${MOOSE_ENV} && \
    echo "# From ${CONTAINER_NAME}" >> ${MOOSE_ENV} && \
    echo ". ${ONEAPI_SETVARS}" >> ${MOOSE_ENV} && \
    echo "export MOOSE_MPICH_DIR=${MPICH_DIR}" >> ${MOOSE_ENV}
