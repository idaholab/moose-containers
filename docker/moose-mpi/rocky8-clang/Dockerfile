#
# moose-mpi-rocky8-clang
#
# Required build arguments:
#
#   BUILD_FROM: FROM image
#   CLANG_VERSION: Version of clang
#   GCC_VERSION: Version of gcc clang installs
#   MPICH_VERSION: Version of mpich
#   URI: URI for the built image
#

ARG BUILD_FROM=unset
FROM $BUILD_FROM

# Path to the moose env script
ARG MOOSE_ENV=/moose_env.sh
# Number of jobs to build with
ARG BUILD_JOBS=4

# Install clang
RUN dnf install -y clang.x86_64 clang-devel.x86_64 clang-libs.x86_64 clang-tools-extra.x86_64 \
        git-clang-format.x86_64 python3.12-clang.x86_64 clang-analyzer.x86_64 libomp.x86_64 lldb && \
    dnf clean all

# Make sure clang and GCC versions match as expected
ARG CLANG_VERSION
ARG GCC_VERSION
RUN test -n "$CLANG_VERSION" && \
    test -n "$GCC_VERSION" && \
    clang --version && \
    clang --version | grep -q "clang version $CLANG_VERSION " && \
    GCC_MAJOR_VERSION="$(echo "$GCC_VERSION" | cut -d'.' -f1)" && \
    . "/opt/rh/gcc-toolset-${GCC_MAJOR_VERSION}/enable" && \
    gcc --version | grep -q "(GCC) ${GCC_VERSION} "

# Install any missing packages from the GCC toolset
RUN GCC_MAJOR_VERSION="$(echo "$GCC_VERSION" | cut -d'.' -f1)" && \
    dnf install -y "gcc-toolset-${GCC_MAJOR_VERSION}" "gcc-toolset-${GCC_MAJOR_VERSION}-gcc" \
        "gcc-toolset-${GCC_MAJOR_VERSION}-gcc-gfortran" "gcc-toolset-${GCC_MAJOR_VERSION}-gcc-c++" \
        "gcc-toolset-${GCC_MAJOR_VERSION}-gdb" make findutils zlib-devel && \
    dnf clean all

# Path to the moose env script
ARG MOOSE_ENV=/moose_env.sh
# Number of jobs to build with
ARG BUILD_JOBS=4

# Install mpich
ARG MPICH_DIR=/opt/mpich
ARG MPICH_VERSION
COPY files/install_mpich.bash /root/install_mpich.bash
RUN . "$MOOSE_ENV" && \
    GCC_MAJOR_VERSION="$(echo "$GCC_VERSION" | cut -d'.' -f1)" && \
    . "/opt/rh/gcc-toolset-${GCC_MAJOR_VERSION}/enable" && \
    /bin/bash /root/install_mpich.bash \
        "$MPICH_VERSION" \
        "$MPICH_DIR"\
        --enable-mpi-api \
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
        F77FLAGS='' && \
    rm /root/install_mpich.bash

# Expose MPI directory and alt GCC as env vars
ARG URI
RUN test -f ${MOOSE_ENV} && \
    GCC_MAJOR_VERSION="$(echo "$GCC_VERSION" | cut -d'.' -f1)" && \
    echo "# From ${URI}" >> ${MOOSE_ENV} && \
    echo ". /opt/rh/gcc-toolset-${GCC_MAJOR_VERSION}/enable" >> ${MOOSE_ENV} && \
    echo "export MOOSE_MPICH_DIR=${MPICH_DIR}" >> ${MOOSE_ENV}
