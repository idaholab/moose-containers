#
# moose-base-ubuntu24
#
# Required build arguments:
#
#   UBUNTU_VERSION: Version of ubuntu
#   ORAS_VERSION: Version of oras
#

ARG UBUNTU_VERSION=unset
FROM ubuntu:${UBUNTU_VERSION}

# Update, install basic packages + python
COPY files/ubuntu_base.bash /root/ubuntu_base.bash
RUN /bin/bash /root/ubuntu_base.bash && rm /root/ubuntu_base.bash

# Install ORAS
COPY files/install_oras.bash /root/install_oras.bash
ARG ORAS_VERSION
RUN /bin/bash /root/install_oras.bash "$ORAS_VERSION" /usr/local/bin && rm /root/install_oras.bash

# Add to environment
ARG MOOSE_ENV=/moose_env.sh
RUN echo "# From moose-base-ubuntu24 ${UBUNTU_VERSION}" >> ${MOOSE_ENV} && \
    chmod +x ${MOOSE_ENV}
