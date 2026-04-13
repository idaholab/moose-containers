FROM ghcr.io/idaholab/moose-base/rocky:8.10_2026.04.12

ARG BUILD_VERSION=2026.04.12

# Install clang
RUN dnf install -y clang.x86_64 clang-devel.x86_64 clang-libs.x86_64 clang-tools-extra.x86_64 \
        git-clang-format.x86_64 python3.12-clang.x86_64 clang-analyzer.x86_64 libomp.x86_64 lldb && \
    dnf clean all

# Make sure version matches as expected
ARG CLANG_VERSION=20.1.8
RUN clang --version | grep -q ${CLANG_VERSION}

# Expose GCC toolset
ARG MOOSE_ENV=/moose_env.sh
ARG GCC_VERSION=14
ARG GCC_ENABLE=/opt/rh/gcc-toolset-${GCC_VERSION}/enable
RUN test -f ${GCC_ENABLE} && \
    test -f ${MOOSE_ENV} && \
    echo "# From moose-mpibase/rocky:8.10-clang${CLANG_VERSION}-mpich${MPICH_VERSION}_${BUILD_VERSION}" >> ${MOOSE_ENV} && \
    echo "source ${GCC_ENABLE}" >> ${MOOSE_ENV}

# Install any missing packages from the GCC toolset
RUN dnf install -y gcc-toolset-${GCC_VERSION} gcc-toolset-${GCC_VERSION}-gcc \
        gcc-toolset-${GCC_VERSION}-gcc-gfortran gcc-toolset-${GCC_VERSION}-gcc-c++ \
        gcc-toolset-${GCC_VERSION}-gdb make findutils zlib-devel && \
    dnf clean all

ARG BUILD_DIR=/root/build
ARG BUILD_JOBS=4

# Install mpich
ARG MPICH_DIR=/opt/mpich
ARG MPICH_VERSION=5.0.1
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
    rm -rf ${BUILD_DIR}
RUN ENV_SCRIPT=${MPICH_DIR}/env.sh && \
    echo "export LD_LIBRARY_PATH=${MPICH_DIR}/lib:\${LD_LIBRARY_PATH}" > ${ENV_SCRIPT} && \
    echo "export MANPATH=${MPICH_DIR}/share/man:\${MANPATH}" >> ${ENV_SCRIPT} && \
    echo "export PATH=${MPICH_DIR}/bin:\${PATH}" >> ${ENV_SCRIPT} && \
    echo "export CC=mpicc CXX=mpicxx FC=mpif90 F90=mpif90 F77=mpif77" >> ${ENV_SCRIPT}
RUN source ${MOOSE_ENV} && \
    source ${MPICH_DIR}/env.sh && \
    mpiexec --version

# Expose MPI directories as env vars
RUN echo "export MOOSE_MPICH_DIR=${MPICH_DIR}" >> ${MOOSE_ENV}
