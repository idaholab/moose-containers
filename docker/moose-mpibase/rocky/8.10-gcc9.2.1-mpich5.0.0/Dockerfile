FROM ghcr.io/idaholab/moose-base/rocky:8.10_0

ARG BUILD_VERSION=0

# Setup build location
ARG BUILD_DIR=/root/build
RUN mkdir ${BUILD_DIR}

# Build jobs
ARG BUILD_JOBS=4
# Path to the moose env script
ARG MOOSE_ENV=/moose_env.sh

# Install GCC
ARG GCC_VERSION=9
RUN dnf install -y gcc-toolset-${GCC_VERSION}

# Add to environment
ARG MOOSE_ENV=/moose_env.sh
RUN test -f ${MOOSE_ENV} && \
    echo "# From moose-mpibase/rocky:8.10-gcc${GCC_VERSION}_${BUILD_VERSION}" >> ${MOOSE_ENV} && \
    echo "source /opt/rh/gcc-toolset-${GCC_VERSION}/enable" >> ${MOOSE_ENV}

# Install mpich
ARG MPICH_DIR=/opt/mpich
ARG MPICH_VERSION=5.0.0
RUN dnf install -y hwloc libnl3 perl
RUN source ${MOOSE_ENV} && \
    set -o pipefail && \
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
    ../configure \
        --prefix=${MPICH_DIR} \
        --enable-mpi-abi 2>&1 | tee ${MPICH_DIR}/logs/configure.log && \
    make -j ${BUILD_JOBS} 2>&1 | tee ${MPICH_DIR}/logs/build.log && \
    make install 2>&1 | tee ${MPICH_DIR}/logs/install.log && \
    rm -rf ${BUILD_DIR}/${MPICH_NAME}
RUN ENV_SCRIPT=${MPICH_DIR}/env.sh && \
    echo "export LD_LIBRARY_PATH=${MPICH_DIR}/lib:\${LD_LIBRARY_PATH}" > ${ENV_SCRIPT} && \
    echo "export MANPATH=${MPICH_DIR}/share/man:\${MANPATH}" >> ${ENV_SCRIPT} && \
    echo "export PATH=${MPICH_DIR}/bin:\${PATH}" >> ${ENV_SCRIPT} && \
    echo "export CC=mpicc CXX=mpicxx FC=mpif90 F90=mpif90 F77=mpif77" >> ${ENV_SCRIPT}
RUN source ${MOOSE_ENV} && \
    source ${MPICH_DIR}/env.sh && \
    mpiexec --version

# Expose MPI directories as env vars
RUN test -f ${MOOSE_ENV} && \
    echo "export MOOSE_MPICH_DIR=${MPICH_DIR}" >> ${MOOSE_ENV}

# Make sure version matches as expected
RUN source ${MOOSE_ENV} && gcc --version | grep -q 9.2.1

# Cleanup
RUN dnf clean all && \
    rm -rf ${BUILD_DIR}
