#
# Used for:
#
#   moose-compiler-ubuntu24-clang
#
# Required build arguments:
#
#   BUILD_FROM: FROM image
#   CONTAINER_NAME: Name for the container
#   CLANG_VERSION: Full version of clang to install
#   GCC_VERSION: Full version of GCC to install for gfortran
#

ARG BUILD_FROM=unset
FROM $BUILD_FROM

# Install clang and gfortran
ARG CLANG_VERSION
ARG GCC_VERSION
RUN test -n "$CLANG_VERSION" && \
    test -n "$GCC_VERSION" && \
    CLANG_MAJOR_VERSION="$(/bin/bash -c "cut -d '.' -f 1,1 <<< $CLANG_VERSION")" && \
    GCC_MAJOR_VERSION="$(/bin/bash -c "cut -d '.' -f 1,1 <<< $GCC_VERSION")" && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc-${GCC_MAJOR_VERSION} \
        g++-${GCC_MAJOR_VERSION} \
        gfortran-${GCC_MAJOR_VERSION} \
        libstdc++-${GCC_MAJOR_VERSION}-dev \
        gnupg \
        lsb-release \
        make \
        software-properties-common && \
    curl -L -O https://apt.llvm.org/llvm.sh && \
    /bin/bash llvm.sh "$CLANG_MAJOR_VERSION" && \
    rm llvm.sh && \
    apt-get install -y --no-install-recommends libomp-${CLANG_MAJOR_VERSION}-dev && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Setup symlinks
ARG CLANG_DIR=/opt/clang
ARG GCC_DIR=/opt/gcc
RUN CLANG_MAJOR_VERSION="$(/bin/bash -c "cut -d '.' -f 1,1 <<< $CLANG_VERSION")" && \
    GCC_MAJOR_VERSION="$(/bin/bash -c "cut -d '.' -f 1,1 <<< $GCC_VERSION")" && \
    mkdir -p "${GCC_DIR}/bin" && \
    ln -s "/usr/lib/llvm-${CLANG_MAJOR_VERSION}" "$CLANG_DIR" && \
    ln -s "/usr/bin/gfortran-${GCC_MAJOR_VERSION}" "${GCC_DIR}/bin/gfortran"

# Test clang version
RUN "${CLANG_DIR}/bin/clang" --version && \
    "${CLANG_DIR}/bin/clang" --version | grep -q "clang version ${CLANG_VERSION}"

# Test gfortran version
RUN "${GCC_DIR}/bin/gfortran" --version && \
    "${GCC_DIR}/bin/gfortran" --version | grep -q ") ${GCC_VERSION}"

# Install valgrind
ARG VALGRIND_DIR=/opt/valgrind
ARG VALGRIND_VERSION=3.27.1
RUN --mount=type=bind,source=files/install_valgrind.bash,target=/root/install_valgrind.bash \
    export CC=${CLANG_DIR}/bin/clang && \
    eval "/bin/bash /root/install_valgrind.bash \"$VALGRIND_VERSION\" \"$VALGRIND_DIR\""

# Setup separate compiler environment
ARG CONTAINER_NAME
ARG MOOSE_ENV=/moose_env.sh
RUN test -n "$CONTAINER_NAME" && \
    test -f "$MOOSE_ENV" && \
    echo "# From ${CONTAINER_NAME}" >> ${MOOSE_ENV} && \
    echo "export PATH=${CLANG_DIR}/bin:${GCC_DIR}/bin:${VALGRIND_DIR}/bin:${PATH}" >> ${MOOSE_ENV} && \
    echo "export CC=${CLANG_DIR}/bin/clang" >> ${MOOSE_ENV} && \
    echo "export CXX=${CLANG_DIR}/bin/clang++" >> ${MOOSE_ENV} && \
    echo "export FC=${GCC_DIR}/bin/gfortran" >> ${MOOSE_ENV} && \
    echo "export F77=${GCC_DIR}/bin/gfortran" >> ${MOOSE_ENV} && \
    . ${MOOSE_ENV} && \
    [ "$(which clang)" = "${CLANG_DIR}/bin/clang" ] && \
    [ "$(which clang++)" = "${CLANG_DIR}/bin/clang++" ] && \
    [ "$(which gfortran)" = "${GCC_DIR}/bin/gfortran" ]
