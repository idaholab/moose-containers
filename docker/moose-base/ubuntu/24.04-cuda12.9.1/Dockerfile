FROM nvidia/cuda:12.9.1-devel-ubuntu24.04

ARG BUILD_VERSION=2026.03.09

# Upgrade base OS
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get dist-upgrade -y

# Install basic packages
RUN apt-get install -y bzip2 git git-lfs tar vim wget rsync hostname jq \
    diffutils file unzip findutils procps xz-utils file which time emacs curl

# Install basic python dependencies and use this python as default
ARG PYTHON_VERSION=3.12
RUN which python${PYTHON_VERSION} && \
    apt-get install -y python3-yaml python3-jinja2 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 100 && \
    python --version | grep ${PYTHON_VERSION}

# Setup build location
ARG BUILD_DIR=/root/build
RUN mkdir ${BUILD_DIR}

# Install oras
ARG ORAS_VERSION=1.3.0
RUN ORAS_TAR=${BUILD_DIR}/oras.tar.gz && \
    ORAS_DIR=${BUILD_DIR}/oras && \
    curl -L https://github.com/oras-project/oras/releases/download/v${ORAS_VERSION}/oras_${ORAS_VERSION}_linux_amd64.tar.gz -o ${ORAS_TAR} && \
    mkdir ${ORAS_DIR} && \
    tar -zxf ${ORAS_TAR} -C ${ORAS_DIR} && \
    rm ${ORAS_TAR} && \
    mv ${ORAS_DIR}/oras /usr/local/bin/ && \
    rm -rf ${ORAS_DIR}

# Cleanup
RUN apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf ${BUILD_DIR}

# Add to environment
ARG MOOSE_ENV=/moose_env.sh
RUN echo "# From moose-base/ubuntu:24.04-cuda12.9.1_${BUILD_VERSION}" >> ${MOOSE_ENV} && \
    echo "export CUDA_DIR=/usr/local/cuda" >> ${MOOSE_ENV} && \
    chmod +x ${MOOSE_ENV}
