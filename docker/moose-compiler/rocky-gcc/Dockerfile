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

# Add to environment
ARG URI
ARG MOOSE_ENV=/moose_env.sh
RUN test -f ${MOOSE_ENV} && \
    test -n "$URI" && \
    GCC_MAJOR_VERSION="$(echo "$GCC_VERSION" | cut -d'.' -f1)" && \
    test -f "/opt/rh/gcc-toolset-${GCC_MAJOR_VERSION}/enable" && \
    echo "# From ${URI}" >> ${MOOSE_ENV} && \
    echo ". /opt/rh/gcc-toolset-${GCC_MAJOR_VERSION}/enable" >> ${MOOSE_ENV}

# Make sure GCC version matches as expected
RUN source ${MOOSE_ENV} && gcc --version | grep -q "(GCC) ${GCC_VERSION} "
