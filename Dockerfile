FROM ubuntu:bionic

USER root

# Set env
ENV DEBIAN_FRONTEND=noninteractive \
    MOZ_HEADLESS=1 \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    FIREFOX_VERSION=69.0.2 \
    GECKODRIVER_VERSION=0.25.0

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
        sudo \
        wget \
        dconf-tools \
        build-essential \
        gcc \
        python-dev \
        python3.7-dev \
        ipython3 \
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

# Copy all files to the container
COPY . /code

WORKDIR /code

RUN mkdir /test_files

RUN mv /usr/bin/geckodriver /usr/bin/geckodriver2 \
    && mv ./utilities/geckodriver /usr/bin/geckodriver \
    && chmod +x /usr/bin/geckodriver

# Install python deps
RUN pip3 install -r pipenv.txt
RUN pipenv install --python 3.7

# Download older firefox nightly
RUN FIREFOX_OLD_DOWNLOAD_URL=$(pipenv run download_old_firefox) \
    && wget -q -O /tmp/firefox_old.tar.bz2 $FIREFOX_OLD_DOWNLOAD_URL \
    && mkdir utilities/firefox-old-nightly \
    && mkdir utilities/firefox-old-nightly-disable-test \
    && tar -C utilities/firefox-old-nightly -xjf /tmp/firefox_old.tar.bz2 \
    && tar -C utilities/firefox-old-nightly-disable-test -xjf /tmp/firefox_old.tar.bz2 \
    && rm /tmp/firefox_old.tar.bz2

RUN FIREFOX_RELEASE_DOWNLOAD_URL=$(pipenv run download_release_firefox) \
    && wget -q -O /tmp/firefox_release.tar.bz2 $FIREFOX_RELEASE_DOWNLOAD_URL \
    && mkdir utilities/firefox-release \
    && tar -C utilities/firefox-release -xjf /tmp/firefox_release.tar.bz2

# Create profile used for update tests
RUN utilities/firefox-old-nightly/firefox/firefox -no-remote -CreateProfile "klaatu-profile-old-base /code/utilities/klaatu-profile-old-base"

RUN utilities/firefox-old-nightly-disable-test/firefox/firefox -no-remote -CreateProfile "klaatu-profile-disable-test /code/utilities/klaatu-profile-disable-test"

RUN utilities/firefox-release/firefox/firefox -no-remote -CreateProfile "klaatu-profile-release-firefox-base /code/utilities/klaatu-profile-release-firefox-base"

RUN firefox -no-remote -CreateProfile "klaatu-profile-current-base /code/utilities/klaatu-profile-current-base"

# Copy prefs needed for test
RUN cp utilities/user.js utilities/klaatu-profile-old-base

RUN cp utilities/user.js utilities/klaatu-profile-current-base

RUN cp utilities/user.js utilities/klaatu-profile-disable-test

RUN cp utilities/user.js utilities/klaatu-profile-release-firefox-base