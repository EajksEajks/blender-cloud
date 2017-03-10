#!/usr/bin/env bash

set -e  # error out when one of the commands in the script errors.

if [ -z "$1" ]; then
    echo "Usage: $0 {host-to-deploy-to}" >&2
    exit 1
fi

DEPLOYHOST="$1"

PILLAR_DIR=$(python <<EOT
from __future__ import print_function
import os.path
import pillar

print(os.path.dirname(os.path.dirname(pillar.__file__)))
EOT
)

ASSETS="$PILLAR_DIR/pillar/web/static/assets/"
TEMPLATES="$PILLAR_DIR/pillar/web/templates/"

if [ ! -d "$ASSETS" ]; then
    echo "Unable to find assets dir $ASSETS"
    exit 1
fi

cd $PILLAR_DIR
if [ $(git rev-parse --abbrev-ref HEAD) != "production" ]; then
    echo "You are NOT on the production branch, refusing to rsync_ui." >&2
    exit 1
fi

echo
echo "*** GULPA GULPA ***"
if [ -x ./node_modules/.bin/gulp ]; then
    ./node_modules/.bin/gulp --production
else
    gulp --production
fi

echo
echo "*** SYNCING ASSETS ***"
rsync -avh $ASSETS root@${DEPLOYHOST}:/data/git/pillar/pillar/web/static/assets/

echo
echo "*** SYNCING TEMPLATES ***"
rsync -avh $TEMPLATES root@${DEPLOYHOST}:/data/git/pillar/pillar/web/templates/
