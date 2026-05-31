#
# Used for:
#
#   moose-compiler-ubuntu24-cuda-gcc
#   moose-compiler-ubuntu24-gcc
#
# Required build arguments:
#
#   BUILD_FROM: FROM image
#   GCC_VERSION: Full version of GCC to install
#   URI: URI for the built image
#

ARG BUILD_FROM=unset
FROM $BUILD_FROM

# Install GCC and basic build utilities
ARG GCC_VERSION
RUN test -n "$GCC_VERSION" && \
    GCC_MAJOR_VERSION="$(/bin/bash -c "cut -d '.' -f 1,1 <<< $GCC_VERSION")" && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc-${GCC_MAJOR_VERSION} \
        g++-${GCC_MAJOR_VERSION} \
        gfortran-${GCC_MAJOR_VERSION} \
        make && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Test GCC version
RUN GCC_MAJOR_VERSION="$(/bin/bash -c "cut -d '.' -f 1,1 <<< $GCC_VERSION")" && \
    "/usr/bin/gcc-${GCC_MAJOR_VERSION}" --version && \
    "/usr/bin/gcc-${GCC_MAJOR_VERSION}" --version | grep -q ") ${GCC_VERSION}"

# Setup separate compiler environment
ARG GCC_DIR=/opt/gcc
ARG URI
ARG MOOSE_ENV=/moose_env.sh
RUN test -n "$URI" && \
    GCC_MAJOR_VERSION="$(/bin/bash -c "cut -d '.' -f 1,1 <<< $GCC_VERSION")" && \
    GCC_BIN="${GCC_DIR}/bin" && \
    mkdir -p "$GCC_BIN" && \
    ln -s "/usr/bin/gcc-${GCC_MAJOR_VERSION}" "${GCC_BIN}/gcc" && \
    ln -s "/usr/bin/g++-${GCC_MAJOR_VERSION}" "${GCC_BIN}/g++" && \
    ln -s "/usr/bin/gfortran-${GCC_MAJOR_VERSION}" "${GCC_BIN}/gfortran" && \
    test -f "$MOOSE_ENV" && \
    echo "# From ${URI}" >> ${MOOSE_ENV} && \
    echo "export PATH=${GCC_BIN}:${PATH}" >> ${MOOSE_ENV} && \
    . ${MOOSE_ENV} && \
    gcc --version | grep ${GCC_VERSION} && \
    g++ --version | grep ${GCC_VERSION} && \
    gfortran --version | grep ${GCC_VERSION}
