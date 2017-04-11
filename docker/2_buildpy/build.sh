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

# Use the docker image to build Python 3.6 and mod-wsgi
GID=$(id -g)
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

# Make sure we can run Python
ldconfig

# Build mod-wsgi-py3 for Python 3.6
cd /dpkg/mod-wsgi-*
./configure --with-python=/opt/python/bin/python3
make -j8 install
mkdir -p /opt/python/mod-wsgi
cp /usr/lib/apache2/modules/mod_wsgi.so /opt/python/mod-wsgi

chown -R $UID:$GID /opt/python/*
EOT

# Strip some stuff we don't need from the Python install.
rm -rf $PYTHONTARGET/lib/python3.*/test
rm -rf $PYTHONTARGET/lib/python3.*/config-3.*/libpython3.*.a
find $PYTHONTARGET/lib -name '*.so.*' -o -name '*.so' | while read libname; do
    chmod u+w "$libname"
    strip "$libname"
done

# Create another docker image which contains the actual Python.
# This one will serve as base for the Wheel builder and the
# production image.
docker build -t armadillica/pillar_py:3.6 -f includepy.docker .
