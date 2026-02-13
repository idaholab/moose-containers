FROM rockylinux/rockylinux:9.7.20251123

# Versions
ARG ORAS_VERSION=1.3.0
# Build location
ARG BUILD_DIR=/root/build
# New python version
ARG MOOSE_PYTHON=/opt/moose_python

# Setup build location
RUN mkdir ${BUILD_DIR}

# Upgrade base OS
RUN dnf upgrade -y

# Install basic packages
RUN dnf install -y bzip2 git git-lfs tar vim wget rsync hostname jq \
    diffutils file unzip findutils procps-ng xz file which

# Install python
RUN dnf install -y python python-devel python-pip python-setuptools
RUN pip3 install pyyaml jinja2

# Install oras
RUN ORAS_TAR=${BUILD_DIR}/oras.tar.gz && \
    ORAS_DIR=${BUILD_DIR}/oras && \
    curl -L https://github.com/oras-project/oras/releases/download/v${ORAS_VERSION}/oras_${ORAS_VERSION}_linux_amd64.tar.gz -o ${ORAS_TAR} && \
    mkdir ${ORAS_DIR} && \
    tar -zxf ${ORAS_TAR} -C ${ORAS_DIR} && \
    rm ${ORAS_TAR} && \
    mv ${ORAS_DIR}/oras /usr/local/bin/ && \
    rm -rf ${ORAS_DIR}

# Cleanup
RUN dnf clean all && \
    rm -rf ${BUILD_DIR}

# Setup empty environment script
RUN touch /moose_env.sh
