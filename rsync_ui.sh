#!/usr/bin/env bash

: ${PILLAR_DIR?"Need to set PILLAR_DIR"}

ASSETS="$PILLAR_DIR/pillar/web/static/assets/"
TEMPLATES="$PILLAR_DIR/pillar/web/templates/"

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
rsync -avh $ASSETS root@cloud.blender.org:/data/git/pillar/pillar/web/static/assets/

echo
echo "*** SYNCING TEMPLATES ***"
rsync -avh $TEMPLATES root@cloud.blender.org:/data/git/pillar/pillar/web/templates/
