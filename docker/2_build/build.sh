#!/usr/bin/env bash

# macOS does not support readlink -f, so we use greadlink instead
if [ $(uname) == 'Darwin' ]; then
    command -v greadlink 2>/dev/null 2>&1 || { echo >&2 "Install greadlink using brew."; exit 1; }
    readlink='greadlink'
else
    readlink='readlink'
fi

TOPDEVDIR="$($readlink -f ../../..)"
echo "Top-level development dir is $TOPDEVDIR"

PYTHON=$($readlink -f ../3_run/python)
WHEELHOUSE="$($readlink -f ../3_run/wheelhouse)"
if [ -z "$WHEELHOUSE" -o -z "$PYTHON" ]; then
    echo "Error, ../3_run might not exist." >&2
    exit 2
fi

mkdir -p "$WHEELHOUSE" "$PYTHON"
echo "Wheelhouse is $WHEELHOUSE"
echo "Python will be built to $PYTHON"

docker build -t pillar_build -f build.docker .
#docker run --rm \
#    -v "$WHEELHOUSE:/data/wheelhouse" \
#    -v "$TOPDEVDIR:/data/topdev" \
#    -v "$PYTHON:/data/python" \
#    pillar_build

# RUN cd Python-3.6.0/ && ./myconfigure
# RUN cd Python-3.6.0/ && make -j8 install
