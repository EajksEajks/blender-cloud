#!/usr/bin/env bash

set -e

# macOS does not support readlink -f, so we use greadlink instead
if [ $(uname) == 'Darwin' ]; then
    command -v greadlink 2>/dev/null 2>&1 || { echo >&2 "Install greadlink using brew."; exit 1; }
    readlink='greadlink'
else
    readlink='readlink'
fi

PYTHONTARGET=$($readlink -f ./python)

mkdir -p "$PYTHONTARGET"
echo "Python will be built to $PYTHONTARGET"

docker build -t pillar_build -f buildpy.docker .

# Use the docker image to build Python 3.6.
GID=$(id --group)
docker run --rm -i \
    -v "$PYTHONTARGET:/opt/python" \
    pillar_build <<EOT
set -e
cd \$PYTHONSOURCE
./configure \
    --prefix=/opt/python \
    --enable-ipv6 \
    --enable-shared \
    --with-ensurepip=upgrade
make -j8 install
chown -R $UID:$GID /opt/python/*
EOT

# Create another docker image which contains the actual Python.
# This one will serve as base for the Wheel builder and the
# production image.
docker build -t pillar_py:3.6 -f includepy.docker .
