#
# Used for:
#
#   moose-compiler-rocky8-gcc
#   moose-compiler-rocky8-cuda-gcc
#   moose-compiler-rocky9-gcc
#
# Required build arguments:
#
#   BUILD_FROM: FROM image
#   CONTAINER_NAME: Name for the container
#   GCC_VERSION: Full version of GCC to install
#   URI: URI for the built image
#

ARG BUILD_FROM=unset
FROM $BUILD_FROM

# GCC and basic build utilities
ARG GCC_VERSION
RUN test -n "$GCC_VERSION" && \
    GCC_MAJOR_VERSION="$(echo "$GCC_VERSION" | cut -d'.' -f1)" && \
    dnf install -y gcc-toolset-${GCC_MAJOR_VERSION} gcc-toolset-${GCC_MAJOR_VERSION}-gcc \
        gcc-toolset-${GCC_MAJOR_VERSION}-gcc-gfortran gcc-toolset-${GCC_MAJOR_VERSION}-gcc-c++ \
        gcc-toolset-${GCC_MAJOR_VERSION}-gdb make findutils zlib-devel && \
    dnf clean all

# Install valgrind
ARG VALGRIND_DIR=/opt/valgrind
ARG VALGRIND_VERSION=3.27.1
RUN --mount=type=bind,source=files/install_valgrind.bash,target=/root/install_valgrind.bash \
    GCC_MAJOR_VERSION="$(echo "$GCC_VERSION" | cut -d'.' -f1)" && \
    . /opt/rh/gcc-toolset-${GCC_MAJOR_VERSION}/enable && \
    eval "/bin/bash /root/install_valgrind.bash \"$VALGRIND_VERSION\" \"$VALGRIND_DIR\""

# Add to environment
ARG CONTAINER_NAME
ARG MOOSE_ENV=/moose_env.sh
RUN test -f ${MOOSE_ENV} && \
    test -n "$CONTAINER_NAME" && \
    GCC_MAJOR_VERSION="$(echo "$GCC_VERSION" | cut -d'.' -f1)" && \
    echo "# From ${CONTAINER_NAME}" >> ${MOOSE_ENV} && \
    echo "export PATH=${VALGRIND_DIR}/bin:${PATH}" >> ${MOOSE_ENV} && \
    echo ". /opt/rh/gcc-toolset-${GCC_MAJOR_VERSION}/enable" >> ${MOOSE_ENV}

# Make sure GCC version matches as expected
RUN source ${MOOSE_ENV} && gcc --version | grep -q "(GCC) ${GCC_VERSION} "
