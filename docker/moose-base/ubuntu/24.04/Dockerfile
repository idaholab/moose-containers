FROM ubuntu:24.04

# Update, install basic packages + python
ARG PYTHON_VERSION=3.12
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get dist-upgrade -y && \
    apt-get install -y --no-install-recommends \
        bzip2 git git-lfs tar vim wget rsync hostname jq diffutils file unzip \
        findutils procps xz-utils file which time curl ca-certificates zlib1g-dev \
        python3 python3-yaml python3-jinja2 && \
    which python${PYTHON_VERSION} && \
    update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 100 && \
    python --version | grep ${PYTHON_VERSION} && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install oras
ARG BUILD_DIR=/root/build
ARG ORAS_VERSION=1.3.0
RUN ORAS_TAR=${BUILD_DIR}/oras.tar.gz && \
    ORAS_DIR=${BUILD_DIR}/oras && \
    mkdir ${BUILD_DIR} && \
    curl -L https://github.com/oras-project/oras/releases/download/v${ORAS_VERSION}/oras_${ORAS_VERSION}_linux_amd64.tar.gz -o ${ORAS_TAR} && \
    mkdir ${ORAS_DIR} && \
    tar -zxf ${ORAS_TAR} -C ${ORAS_DIR} && \
    rm ${ORAS_TAR} && \
    mv ${ORAS_DIR}/oras /usr/local/bin/ && \
    rm -rf ${ORAS_DIR} && \
    rm -rf ${BUILD_DIR}

# Setup empty environment script
RUN echo "#!/bin/sh" > /moose_env.sh && chmod +x /moose_env.sh
