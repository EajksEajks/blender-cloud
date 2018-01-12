#!/usr/bin/env bash

set -e  # error out when one of the commands in the script errors.

if [ -z "$1" ]; then
    echo "Usage: $0 {host-to-deploy-to}" >&2
    exit 1
fi

DEPLOYHOST="$1"

# macOS does not support readlink -f, so we use greadlink instead
if [[ `uname` == 'Darwin' ]]; then
    command -v greadlink 2>/dev/null 2>&1 || { echo >&2 "Install greadlink using brew."; exit 1; }
    readlink='greadlink'
else
    readlink='readlink'
fi

BLENDER_CLOUD_DIR="$(dirname "$($readlink -f "$0")")"
if [ ! -d "$BLENDER_CLOUD_DIR" ]; then
    echo "Unable to find Blender Cloud dir '$BLENDER_CLOUD_DIR'"
    exit 1
fi

BLENDER_CLOUD_ASSETS="$BLENDER_CLOUD_DIR/cloud/static/"
BLENDER_CLOUD_TEMPLATES="$BLENDER_CLOUD_DIR/cloud/templates/"

if [ ! -d "$BLENDER_CLOUD_ASSETS" ]; then
    echo "Unable to find assets dir $BLENDER_CLOUD_ASSETS"
    exit 1
fi

cd $BLENDER_CLOUD_DIR
if [ $(git rev-parse --abbrev-ref HEAD) != "production" ]; then
    echo "You are NOT on the production branch, refusing to rsync_ui." >&2
    exit 1
fi

PILLAR_DIR=$(python <<EOT
from __future__ import print_function
import os.path
import pillar

print(os.path.dirname(os.path.dirname(pillar.__file__)))
EOT
)

PILLAR_ASSETS="$PILLAR_DIR/pillar/web/static/assets/"
PILLAR_TEMPLATES="$PILLAR_DIR/pillar/web/templates/"

if [ ! -d "$PILLAR_ASSETS" ]; then
    echo "Unable to find assets dir $PILLAR_ASSETS"
    exit 1
fi

cd $PILLAR_DIR
if [ $(git rev-parse --abbrev-ref HEAD) != "production" ]; then
    echo "Pillar is NOT on the production branch, refusing to rsync_ui." >&2
    exit 1
fi

echo
echo "*** GULPA GULPA PILLAR ***"
# TODO(Pablo): this command fails when passing the --production CLI
# arg.
./gulp

echo
echo "*** SYNCING PILLAR_ASSETS ***"
rsync -avh $PILLAR_ASSETS root@${DEPLOYHOST}:/data/git/pillar/pillar/web/static/assets/ --delete-after

echo
echo "*** SYNCING PILLAR_TEMPLATES ***"
rsync -avh $PILLAR_TEMPLATES root@${DEPLOYHOST}:/data/git/pillar/pillar/web/templates/ --delete-after


cd $BLENDER_CLOUD_DIR

echo
echo "*** GULPA GULPA BLENDER_CLOUD ***"
./gulp --production

echo
echo "*** SYNCING BLENDER_CLOUD_ASSETS ***"
# Exclude files managed by Git.
rsync -avh $BLENDER_CLOUD_ASSETS --exclude js/vendor/ root@${DEPLOYHOST}:/data/git/blender-cloud/cloud/static/ --delete-after

echo
echo "*** SYNCING BLENDER_CLOUD_TEMPLATES ***"
rsync -avh $BLENDER_CLOUD_TEMPLATES root@${DEPLOYHOST}:/data/git/blender-cloud/cloud/templates/ --delete-after
