FROM ghcr.io/idaholab/moose-base/rocky:9.7_0

# Versions
ARG GCC_VERSION=13
# Path to the moose env script
ARG MOOSE_ENV=/moose_env.sh

# GCC 13 and basic build utilities
RUN dnf install -y gcc-toolset-${GCC_VERSION} gcc-toolset-${GCC_VERSION}-gcc \
    gcc-toolset-${GCC_VERSION}-gcc-gfortran gcc-toolset-${GCC_VERSION}-gcc-c++ \
    gcc-toolset-${GCC_VERSION}-gdb make findutils zlib-devel

# Cleanup
RUN dnf clean all

# Add to environment
RUN test -f ${MOOSE_ENV} && \
    echo "# From moose-base/rocky:9.7-gcc13_0" >> ${MOOSE_ENV} && \
    echo "source /opt/rh/gcc-toolset-13/enable" >> ${MOOSE_ENV}
