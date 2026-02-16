FROM ghcr.io/idaholab/moose-compilerbase/rocky:8.10-gcc13.3.1_0

ARG BUILD_VERSION=0

# Setup build location
ARG BUILD_DIR=/root/build
RUN mkdir ${BUILD_DIR}

# Setup environment addition
ARG MPICH_VERSION=4.3.2
ARG ONEAPI_VERSION=2025.3.2
ARG MOOSE_ENV=/moose_env.sh
RUN test -f ${MOOSE_ENV} && \
    echo "# From moose-mpibase/rocky:8.10-oneapi${ONEAPI_VERSION}-mpich${MPICH_VERSION}_${BUILD_VERSION}" >> ${MOOSE_ENV}

# Install intel oneapi
COPY oneAPI.repo /etc/yum.repos.d/oneAPI.repo
RUN dnf install -y intel-oneapi-compiler-dpcpp-cpp intel-oneapi-openmp intel-oneapi-compiler-fortran

# Store the variables we need from the "setvars.sh" script and add to environment
COPY setup_vars.bash /root/setup_vars.bash
RUN chmod +x /root/setup_vars.bash && \
    /root/setup_vars.bash /opt/intel/oneapi/moose_setvars.sh && \
    rm /root/setup_vars.bash && \
    echo "source /opt/intel/oneapi/moose_setvars.sh" >> ${MOOSE_ENV}

# Check oneapi version
RUN source ${MOOSE_ENV} && icx --version | grep -q ${ONEAPI_VERSION}

# Build jobs
ARG BUILD_JOBS=4

# Install mpich
ARG MPICH_DIR=/opt/mpich
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
        CC=icx CXX=icpx FC=ifx F77=ifx F90=ifx \
        --prefix=${MPICH_DIR} \
        --with-device=ch3:nemesis 2>&1 | tee ${MPICH_DIR}/logs/configure.log && \
    make -j ${BUILD_JOBS} 2>&1 | tee ${MPICH_DIR}/logs/build.log && \
    make install 2>&1 | tee ${MPICH_DIR}/logs/install.log && \
    rm -rf ${BUILD_DIR}/${MPICH_NAME}
RUN ENV_SCRIPT=${MPICH_DIR}/env.sh && \
    echo "export LD_LIBRARY_PATH=${MPICH_DIR}/lib:\${LD_LIBRARY_PATH}" > ${ENV_SCRIPT} && \
    echo "export MANPATH=${MPICH_DIR}/share/man:\${MANPATH}" >> ${ENV_SCRIPT} && \
    echo "export PATH=${MPICH_DIR}/bin:\${PATH}" >> ${ENV_SCRIPT} && \
    echo "export CC=icx CXX=icpx FC=ifx F77=ifx F90=ifx" >> ${ENV_SCRIPT}
RUN source ${MOOSE_ENV} && \
    source ${MPICH_DIR}/env.sh && \
    mpiexec --version

# Expose MPI directory as an env var
RUN echo "export MOOSE_MPICH_DIR=${MPICH_DIR}" >> ${MOOSE_ENV}

# Cleanup
RUN dnf clean all && rm -rf ${BUILD_DIR}
