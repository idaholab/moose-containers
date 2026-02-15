FROM ghcr.io/idaholab/moose-compilerbase/rocky:8.10-gcc13.3.1_0

ARG BUILD_VERSION=0

# Setup build location
ARG BUILD_DIR=/root/build
RUN mkdir ${BUILD_DIR}

# Install clang
RUN dnf install -y clang.x86_64 clang-devel.x86_64 clang-libs.x86_64 clang-tools-extra.x86_64 \
    git-clang-format.x86_64 python3.12-clang.x86_64 clang-analyzer.x86_64 libomp.x86_64 lldb

# Make sure version matches as expected
RUN clang --version | grep -q 20.1.8

# Build jobs
ARG BUILD_JOBS=4
# Path to the moose env script
ARG MOOSE_ENV=/moose_env.sh

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
        --enable-mpi-abi \
        CC=clang \
        CXX=clang++ \
        FC=gfortran \
        F77=gfortran \
        F90=gfortran \
        CFLAGS='' \
        CXXFLAGS='' \
        FFLAGS='-fallow-argument-mismatch' \
        FCFLAGS='-fallow-argument-mismatch' \
        F90FLAGS='' \
        F77FLAGS='' 2>&1 | tee ${MPICH_DIR}/logs/configure.log && \
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
    echo "# From moose-mpibase/rocky:8.10-clang14-mpich${MPICH_VERSION}_${BUILD_VERSION}" >> ${MOOSE_ENV} && \
    echo "export MOOSE_MPICH_DIR=${MPICH_DIR}" >> ${MOOSE_ENV}

# Cleanup
RUN dnf clean all && rm -rf ${BUILD_DIR}
