FROM ghcr.io/idaholab/moose-base/rocky:8.10_0

ARG BUILD_VERSION=0

# GCC 13 and basic build utilities
ARG GCC_VERSION=13
RUN dnf install -y gcc-toolset-${GCC_VERSION} gcc-toolset-${GCC_VERSION}-gcc \
    gcc-toolset-${GCC_VERSION}-gcc-gfortran gcc-toolset-${GCC_VERSION}-gcc-c++ \
    gcc-toolset-${GCC_VERSION}-gdb make findutils zlib-devel

# Add to environment
ARG MOOSE_ENV=/moose_env.sh
RUN test -f ${MOOSE_ENV} && \
    echo "# From moose-base/rocky:8.10-gcc${GCC_VERSION}_${BUILD_VERSION}" >> ${MOOSE_ENV} && \
    echo "source /opt/rh/gcc-toolset-${GCC_VERSION}/enable" >> ${MOOSE_ENV}

# Make sure GCC version matches as expected
RUN source ${MOOSE_ENV} && gcc --version | grep -q 13.3.1

# Cleanup
RUN dnf clean all
