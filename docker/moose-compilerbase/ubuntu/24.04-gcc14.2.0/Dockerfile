FROM ghcr.io/idaholab/moose-base/ubuntu:24.04_2026.03.24

ARG BUILD_VERSION=2026.03.24

# Path to the moose env script
ARG MOOSE_ENV=/moose_env.sh

# Install GCC and basic build utilities
ENV GCC_VERSION=14.2.0
RUN GCC_MAJOR_VERSION="$(/bin/bash -c "cut -d '.' -f 1,1 <<< $GCC_VERSION")" && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc-${GCC_MAJOR_VERSION} \
        g++-${GCC_MAJOR_VERSION} \
        gfortran-${GCC_MAJOR_VERSION} \
        make && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Setup separate compiler environment
ARG GCC_DIR=/opt/gcc
RUN GCC_MAJOR_VERSION="$(/bin/bash -c "cut -d '.' -f 1,1 <<< $GCC_VERSION")" && \
    GCC_BIN=${GCC_DIR}/bin && \
    mkdir -p ${GCC_BIN} && \
    ln -s /usr/bin/gcc-${GCC_MAJOR_VERSION} ${GCC_BIN}/gcc && \
    ln -s /usr/bin/g++-${GCC_MAJOR_VERSION} ${GCC_BIN}/g++ && \
    ln -s /usr/bin/gfortran-${GCC_MAJOR_VERSION} ${GCC_BIN}/gfortran && \
    test -f ${MOOSE_ENV} && \
    echo "# From moose-compilerbase/ubuntu:24.04-gcc${GCC_VERSION}_${BUILD_VERSION}" >> ${MOOSE_ENV} && \
    echo "export PATH=${GCC_BIN}:${PATH}" >> ${MOOSE_ENV} && \
    . ${MOOSE_ENV} && \
    gcc --version | grep ${GCC_VERSION} && \
    g++ --version | grep ${GCC_VERSION} && \
    gfortran --version | grep ${GCC_VERSION}
