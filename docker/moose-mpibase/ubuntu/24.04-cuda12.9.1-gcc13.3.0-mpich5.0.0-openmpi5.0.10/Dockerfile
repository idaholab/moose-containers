FROM ghcr.io/idaholab/moose-compilerbase/ubuntu:24.04-cuda12.9.1-gcc13.3.0_2026.03.19

ARG BUILD_VERSION=2026.03.19
ARG GCC_VERSION=13.3.0

# Setup build location
ARG BUILD_DIR=/root/build
RUN mkdir ${BUILD_DIR}

# Build jobs
ARG BUILD_JOBS=4
# Path to the moose env script
ARG MOOSE_ENV=/moose_env.sh

# Install mpich
ARG MPICH_DIR=/opt/mpich
ARG MPICH_VERSION=5.0.0
RUN apt-get update && apt-get install -y patch
RUN . ${MOOSE_ENV} && \
    cd ${BUILD_DIR} && \
    MPICH_MAJOR_VERSION="$(/bin/bash -c "cut -d '.' -f 1,2 <<< ${MPICH_VERSION}")" && \
    MPICH_NAME="mpich-${MPICH_VERSION}" && \
    MPICH_URL="https://www.mpich.org/static/downloads/${MPICH_VERSION}/${MPICH_NAME}.tar.gz" && \
    MPICH_TAR=${BUILD_DIR}/mpich.tar.gz && \
    mkdir -p ${MPICH_DIR}/logs && \
    curl -L ${MPICH_URL} -o ${MPICH_TAR} && \
    tar xf ${MPICH_TAR} -C ${BUILD_DIR} && \
    rm $MPICH_TAR && \
    cd ${BUILD_DIR}/${MPICH_NAME} && \
    curl -L https://github.com/pmodels/mpich/commit/8da0072533ad8be55fbaccdd9fe917908f1ea8a7.patch | patch -p1 && \
    mkdir build && \
    cd build && \
    ../configure \
        --prefix=${MPICH_DIR} \
        --with-cuda=${CUDA_DIR} \
        --enable-mpi-abi \
        --with-device=ch4:ucx 2>&1 | tee ${MPICH_DIR}/logs/configure.log && \
    make -j ${BUILD_JOBS} 2>&1 | tee ${MPICH_DIR}/logs/build.log && \
    make install 2>&1 | tee ${MPICH_DIR}/logs/install.log && \
    rm -rf ${BUILD_DIR}/${MPICH_NAME}
# Setup and test environment script
RUN ENV_SCRIPT=${MPICH_DIR}/env.sh && \
    echo "export LD_LIBRARY_PATH=${MPICH_DIR}/lib:\${LD_LIBRARY_PATH}" > ${ENV_SCRIPT} && \
    echo "export MANPATH=${MPICH_DIR}/share/man:\${MANPATH}" >> ${ENV_SCRIPT} && \
    echo "export PATH=${MPICH_DIR}/bin:\${PATH}" >> ${ENV_SCRIPT} && \
    echo "export CC=mpicc CXX=mpicxx FC=mpif90 F90=mpif90 F77=mpif77" >> ${ENV_SCRIPT} && \
    . ${MOOSE_ENV} && \
    . ${ENV_SCRIPT} && \
    mpiexec --version | grep ${MPICH_VERSION} && \
    mpicc --version | grep ${GCC_VERSION} && \
    mpic++ --version | grep ${GCC_VERSION} && \
    mpifort --version | grep ${GCC_VERSION}

# Install openmpi
ARG OPENMPI_DIR=/opt/openmpi
ARG OPENMPI_VERSION=5.0.10
RUN . ${MOOSE_ENV} && \
    cd ${BUILD_DIR} && \
    OPENMPI_MAJOR_VERSION="$(/bin/bash -c "cut -d '.' -f 1,2 <<< ${OPENMPI_VERSION}")" && \
    OPENMPI_NAME="openmpi-${OPENMPI_VERSION}" && \
    OPENMPI_URL="https://download.open-mpi.org/release/open-mpi/v${OPENMPI_MAJOR_VERSION}/${OPENMPI_NAME}.tar.gz" && \
    OPENMPI_TAR=${BUILD_DIR}/openmpi.tar.gz && \
    mkdir -p ${OPENMPI_DIR}/logs && \
    curl -L ${OPENMPI_URL} -o ${OPENMPI_TAR} && \
    tar xf ${OPENMPI_TAR} -C ${BUILD_DIR} && \
    rm $OPENMPI_TAR && \
    cd ${BUILD_DIR}/${OPENMPI_NAME} && \
    mkdir build && \
    cd build && \
    ../configure \
        --prefix=${OPENMPI_DIR} \
        --with-cuda=${CUDA_DIR} 2>&1 | tee ${OPENMPI_DIR}/logs/configure.log && \
    make -j ${BUILD_JOBS} 2>&1 | tee ${OPENMPI_DIR}/logs/build.log && \
    make install 2>&1 | tee ${OPENMPI_DIR}/logs/install.log && \
    rm -rf ${BUILD_DIR}/${OPENMPI_NAME}
# Setup and test environment script
RUN ENV_SCRIPT=${OPENMPI_DIR}/env.sh && \
    echo "export LD_LIBRARY_PATH=${OPENMPI_DIR}/lib:\${LD_LIBRARY_PATH}" > ${ENV_SCRIPT} && \
    echo "export MANPATH=${OPENMPI_DIR}/share/man:\${MANPATH}" >> ${ENV_SCRIPT} && \
    echo "export PATH=${OPENMPI_DIR}/bin:\${PATH}" >> ${ENV_SCRIPT} && \
    echo "export CC=mpicc CXX=mpicxx FC=mpif90 F90=mpif90 F77=mpif77" >> ${ENV_SCRIPT} && \
    . ${MOOSE_ENV} && \
    . ${ENV_SCRIPT} && \
    mpiexec --version | grep "(Open MPI) ${OPENMPI_VERSION}" && \
    ompi_info | grep "Open MPI: ${OPENMPI_VERSION}" && \
    mpicc --version | grep ${GCC_VERSION} && \
    mpic++ --version | grep ${GCC_VERSION} && \
    mpifort --version | grep ${GCC_VERSION}

# Cleanup
RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf ${BUILD_DIR}
