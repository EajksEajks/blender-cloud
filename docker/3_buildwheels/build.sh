#!/usr/bin/env bash

DOCKER_IMAGE_NAME=armadillica/pillar_wheelbuilder

set -e

# macOS does not support readlink -f, so we use greadlink instead
if [ $(uname) == 'Darwin' ]; then
    command -v greadlink 2>/dev/null 2>&1 || { echo >&2 "Install greadlink using brew."; exit 1; }
    readlink='greadlink'
else
    readlink='readlink'
fi

TOPDEVDIR="$($readlink -f ../../..)"
echo "Top-level development dir is $TOPDEVDIR"

WHEELHOUSE="$($readlink -f ../4_run/wheelhouse)"
if [ -z "$WHEELHOUSE" ]; then
    echo "Error, ../4_run might not exist." >&2
    exit 2
fi

echo "Wheelhouse is $WHEELHOUSE"
mkdir -p "$WHEELHOUSE"
rm -f "$WHEELHOUSE"/*

docker build -t $DOCKER_IMAGE_NAME:latest .

GID=$(id -g)
docker run --rm -i \
    -v "$WHEELHOUSE:/data/wheelhouse" \
    -v "$TOPDEVDIR:/data/topdev" \
    $DOCKER_IMAGE_NAME <<EOT
set -e
pip3 install wheel poetry

# Build wheels for all dependencies.
cd /data/topdev/blender-cloud

poetry install --no-dev

# Apparently pip doesn't like projects without setup.py, so it think we have 'pillar-svnman' as
# requirement (because that's the name of the directory). We have to grep that out.
poetry run pip3 freeze | grep -v '\(pillar\)\|\(^-[ef] \)' > \$WHEELHOUSE/requirements.txt

pip3 wheel --wheel-dir=\$WHEELHOUSE -r \$WHEELHOUSE/requirements.txt
chown -R $UID:$GID \$WHEELHOUSE
EOT

# Remove our own projects, they shouldn't be installed as wheel (for now).
rm -f $WHEELHOUSE/{attract,flamenco,pillar,pillarsdk}*.whl

echo "Build of $DOCKER_IMAGE_NAME:latest is done."
