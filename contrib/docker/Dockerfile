FROM debian:jessie

MAINTAINER Julien Girardin version: 0.1

COPY jessie_backports.list              /etc/apt/sources.list.d/
COPY stretch.list                       /etc/apt/sources.list.d/
COPY preferences_d_jessie               /etc/apt/preferences.d/jessie
COPY preferences_d_django               /etc/apt/preferences.d/django
COPY preferences_d_djangorestframework  /etc/apt/preferences.d/djangorestframework
COPY preferences_d_ansible              /etc/apt/preferences.d/ansible
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    vim \
    git \
    sqlite \
    sudo \
    ansible \
    sshpass

# Python2 package
RUN apt-get update && apt-get install -y \
    python-django \
    python-djangorestframework \
    python-redis \
    python-pip \
    python-dev
RUN pip install channels

# Python3 package
RUN apt-get update && apt-get install -y \
    python3-django \
    python3-djangorestframework \
    python3-redis \
    python3-pip \
    python3-dev
RUN pip3 install channels

RUN useradd -ms /bin/bash user
RUN echo 'user  ALL=(ALL)   NOPASSWD: ALL' > /etc/sudoers.d/user

WORKDIR /home/user
USER user
