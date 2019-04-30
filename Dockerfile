FROM ubuntu:xenial

USER root

# Set env
ENV DEBIAN_FRONTEND=noninteractive \
    MOZ_HEADLESS=1 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    FIREFOX_VERSION=65.0 \
    GECKODRIVER_VERSION=0.24.0

# Install requirements to install tools
RUN dependencies=' \
        bzip2 \
        ca-certificates \
        curl \
        firefox \
        python3.7 \
        python3-pip \
        python-setuptools \
        python-wheel \
        wget \
    ' \
    && set -x \
    && apt-get -qq update && apt-get -qq install -y software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get -qq update && apt-get -qq install --no-install-recommends -y $dependencies \
    && apt-get -y purge firefox \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/*


# Install Firefox and Geckodriver
RUN INSTALLER_DOWNLOAD_URL=https://raw.githubusercontent.com/hackebrot/install-firefox/master/install-firefox.sh \
    && curl $INSTALLER_DOWNLOAD_URL -sSf | sh -s -- --firefox $FIREFOX_VERSION --geckodriver $GECKODRIVER_VERSION

# Update to firefox nightly
ARG FIREFOX_DOWNLOAD_URL=https://download.mozilla.org/?product=firefox-nightly-latest-ssl&lang=en-US&os=linux64
RUN wget --no-verbose -O /tmp/firefox.tar.bz2 $FIREFOX_DOWNLOAD_URL \
    && tar -C /opt -xjf /tmp/firefox.tar.bz2 \
    && rm /tmp/firefox.tar.bz2 \
    && mv /opt/firefox /opt/firefox-nightly \
    && ln -fs /opt/firefox-nightly/firefox /usr/bin/firefox

# Install Tox
RUN pip3 install tox

# Create user with a home directory
ENV HOME /home/user
RUN useradd --create-home --home-dir $HOME user

# Copy all files to the container
COPY . $HOME/code/

# Change file permissions to user
RUN chown -R user:user $HOME

WORKDIR $HOME/code

USER user
