FROM ghcr.io/idaholab/moose-base/rocky:8.10-cuda12.9.1_2026.04.12

ARG BUILD_VERSION=2026.04.12

# GCC 13 and basic build utilities
ARG GCC_VERSION=13
RUN dnf install -y gcc-toolset-${GCC_VERSION} gcc-toolset-${GCC_VERSION}-gcc \
        gcc-toolset-${GCC_VERSION}-gcc-gfortran gcc-toolset-${GCC_VERSION}-gcc-c++ \
        gcc-toolset-${GCC_VERSION}-gdb make findutils zlib-devel && \
    dnf clean all

# Add to environment
ARG MOOSE_ENV=/moose_env.sh
ARG MPICH_VERSION=5.0.1
ARG OPENMPI_VERSION=5.0.10
RUN test -f ${MOOSE_ENV} && \
    echo "# From moose-mpibase/rocky:8.10-cuda12.9.1-gcc${GCC_VERSION}-mpich${MPICH_VERSION}-openmpi${OPENMPI_VERSION}_${BUILD_VERSION}" >> ${MOOSE_ENV} && \
    echo "source /opt/rh/gcc-toolset-${GCC_VERSION}/enable" >> ${MOOSE_ENV}

ARG BUILD_DIR=/root/build
ARG BUILD_JOBS=4

# Install mpich
ARG MPICH_DIR=/opt/mpich
RUN source ${MOOSE_ENV} && \
    set -o pipefail && \
    mkdir ${BUILD_DIR} && \
    cd ${BUILD_DIR} && \
    MPICH_MAJOR_VERSION=$(cut -d '.' -f 1,2 <<< "${MPICH_VERSION}") && \
    MPICH_NAME="mpich-${MPICH_VERSION}" && \
    MPICH_URL="https://www.mpich.org/static/downloads/${MPICH_VERSION}/${MPICH_NAME}.tar.gz" && \
    MPICH_TAR=${BUILD_DIR}/mpich.tar.gz && \
    mkdir -p ${MPICH_DIR}/logs && \
    curl -L ${MPICH_URL} -o ${MPICH_TAR} && \
    tar xf ${MPICH_TAR} -C ${BUILD_DIR} && \
    rm $MPICH_TAR && \
    cd ${BUILD_DIR}/${MPICH_NAME} && \
    mkdir build && \
    cd build && \
    ../configure --prefix=${MPICH_DIR} \
        --with-cuda=${CUDA_DIR} \
        --enable-mpi-abi \
        --with-device=ch4:ucx 2>&1 | tee ${MPICH_DIR}/logs/configure.log && \
    make -j ${BUILD_JOBS} 2>&1 | tee ${MPICH_DIR}/logs/build.log && \
    make install 2>&1 | tee ${MPICH_DIR}/logs/install.log && \
    rm -rf ${BUILD_DIR}
RUN ENV_SCRIPT=${MPICH_DIR}/env.sh && \
    echo "export LD_LIBRARY_PATH=${MPICH_DIR}/lib:\${LD_LIBRARY_PATH}" > ${ENV_SCRIPT} && \
    echo "export MANPATH=${MPICH_DIR}/share/man:\${MANPATH}" >> ${ENV_SCRIPT} && \
    echo "export PATH=${MPICH_DIR}/bin:\${PATH}" >> ${ENV_SCRIPT} && \
    echo "export CC=mpicc CXX=mpicxx FC=mpif90 F90=mpif90 F77=mpif77" >> ${ENV_SCRIPT}
RUN source ${MOOSE_ENV} && \
    source ${MPICH_DIR}/env.sh && \
    LD_LIBRARY_PATH=${CUDA_DIR}/compat:${LD_LIBRARY_PATH} mpiexec --version

# Install openmpi
ARG OPENMPI_DIR=/opt/openmpi
RUN source ${MOOSE_ENV} && \
    set -o pipefail && \
    mkdir ${BUILD_DIR} && \
    cd ${BUILD_DIR} && \
    OPENMPI_MAJOR_VERSION=$(cut -d '.' -f 1,2 <<< "${OPENMPI_VERSION}") && \
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
    rm -rf ${BUILD_DIR}
RUN ENV_SCRIPT=${OPENMPI_DIR}/env.sh && \
    echo "export LD_LIBRARY_PATH=${OPENMPI_DIR}/lib:\${LD_LIBRARY_PATH}" > ${ENV_SCRIPT} && \
    echo "export MANPATH=${OPENMPI_DIR}/share/man:\${MANPATH}" >> ${ENV_SCRIPT} && \
    echo "export PATH=${OPENMPI_DIR}/bin:\${PATH}" >> ${ENV_SCRIPT} && \
    echo "export CC=mpicc CXX=mpicxx FC=mpif90 F90=mpif90 F77=mpif77" >> ${ENV_SCRIPT}
RUN source ${MOOSE_ENV} && \
    source ${OPENMPI_DIR}/env.sh && \
    mpiexec --version && \
    ompi_info

# Expose MPI directories as env vars
RUN test -f ${MOOSE_ENV} && \
    echo "export MOOSE_MPICH_DIR=${MPICH_DIR}" >> ${MOOSE_ENV} && \
    echo "export MOOSE_OPENMPI_DIR=${OPENMPI_DIR}" >> ${MOOSE_ENV}
