FROM ghcr.io/idaholab/moose-base/rocky:8.10_0

ARG BUILD_VERSION=0

# Setup build location
ARG BUILD_DIR=/root/build
RUN mkdir ${BUILD_DIR}

# Build jobs
ARG BUILD_JOBS=4
# Path to the moose env script
ARG MOOSE_ENV=/moose_env.sh

ARG MPICH_VERSION=5.0.0
ARG MOOSE_ENV=/moose_env.sh

# Install gcc for building clang
ARG GCC_VERSION=11
RUN dnf install -y gcc-toolset-${GCC_VERSION}

# Add new gcc to environment
RUN test -f ${MOOSE_ENV} && \
    echo "# From moose-mpibase/rocky:8.10-clang${CLANG_VERSION}-mpich${MPICH_VERSION}_${BUILD_VERSION}" >> ${MOOSE_ENV} && \
    echo "source /opt/rh/gcc-toolset-${GCC_VERSION}/enable" >> ${MOOSE_ENV}

# Install clang
ARG CLANG_VERSION=14.0.6
ARG LLVM_DIR=/opt/llvm
RUN dnf install -y cmake && \
    source ${MOOSE_ENV} && \
    cd ${BUILD_DIR} && \
    git clone --depth 1 --branch llvmorg-${CLANG_VERSION} https://github.com/llvm/llvm-project && \
    cd llvm-project && \
    mkdir llvm-build && \
    cd llvm-build && \
    GCC_DIR=/opt/rh/gcc-toolset-${GCC_VERSION}/root && \
    cmake ../llvm -G 'Unix Makefiles' \
      -DCMAKE_BUILD_TYPE=Release \
      -DLLVM_ENABLE_PROJECTS='clang;clang-tools-extra;compiler-rt;libcxx;libcxxabi;libunwind;openmp;lldb' \
      -DCMAKE_INSTALL_PREFIX=${LLVM_DIR}  \
      -DCMAKE_INSTALL_RPATH:STRING=${LLVM_DIR}/lib \
      -DCMAKE_INSTALL_NAME_DIR:STRING=${LLVM_DIR}/lib \
      -DCMAKE_BUILD_WITH_INSTALL_RPATH=1 \
      -DGCC_INSTALL_PREFIX=${GCC_DIR} \
      -DCMAKE_C_COMPILER=${GCC_DIR}/bin/gcc \
      -DCMAKE_CXX_COMPILER=${GCC_DIR}/bin/g++ \
      -DCMAKE_CXX_LINK_FLAGS="-L${GCC_DIR}/lib -Wl,-rpath,${GCC_DIR}/lib" && \
    make -j ${BUILD_JOBS} && \
    make install

# Add to environment
RUN echo "export PATH=${LLVM_DIR}/bin:\${PATH}" >> ${MOOSE_ENV} && \
    echo "export LD_LIBRARY_PATH=${LLVM_DIR}/lib:\${LD_LIBRARY_PATH}" >> ${MOOSE_ENV}

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
    echo "export MOOSE_MPICH_DIR=${MPICH_DIR}" >> ${MOOSE_ENV}

# Cleanup
RUN dnf clean all && rm -rf ${BUILD_DIR}
