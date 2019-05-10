#!/bin/bash -e

STAGING_BRANCH=${STAGING_BRANCH:-production}

# macOS does not support readlink -f, so we use greadlink instead
if [[ `uname` == 'Darwin' ]]; then
    command -v greadlink 2>/dev/null 2>&1 || { echo >&2 "Install greadlink using brew."; exit 1; }
    readlink='greadlink'
else
    readlink='readlink'
fi

ROOT="$(dirname "$(dirname "$($readlink -f "$0")")")"
STAGINGDIR="$ROOT/docker/4_run/staging"
PROJECT_NAME="$(basename $ROOT)"

if [ -e $STAGINGDIR ]; then
    echo "$STAGINGDIR already exists, press [ENTER] to destroy and re-install, Ctrl+C to abort."
    read dummy
    rm -rf $STAGINGDIR
else
    echo -n "Installing into $STAGINGDIR… "
    echo "press [ENTER] to continue, Ctrl+C to abort."
    read dummy
fi

cd ${ROOT}
mkdir -p $STAGINGDIR
REMOTE_ROOT="$STAGINGDIR/$PROJECT_NAME"

if [ -z "$SKIP_BRANCH_CHECK" ]; then
    # Check that we're on production branch.
    if [ $(git rev-parse --abbrev-ref HEAD) != "$STAGING_BRANCH" ]; then
        echo "You are NOT on the $STAGING_BRANCH branch, refusing to stage." >&2
        exit 1
    fi

    # Check that production branch has been pushed.
    if [ -n "$(git log origin/$STAGING_BRANCH..$STAGING_BRANCH --oneline)" ]; then
        echo "WARNING: not all changes to the $STAGING_BRANCH branch have been pushed."
        echo "Press [ENTER] to continue staging current origin/$STAGING_BRANCH, CTRL+C to abort."
        read dummy
    fi
fi

function find_module()
{
    MODULE_NAME=$1
    MODULE_DIR=$(python <<EOT
from __future__ import print_function
import os.path
try:
    import ${MODULE_NAME}
except ImportError:
    raise SystemExit('${MODULE_NAME} not found on Python path. Are you in the correct venv?')

print(os.path.dirname(os.path.dirname(${MODULE_NAME}.__file__)))
EOT
)
    echo $MODULE_DIR
}

# Find our modules
echo "==================================================================="
echo "LOCAL MODULE LOCATIONS"
PILLAR_DIR=$(find_module pillar)
ATTRACT_DIR=$(find_module attract)
FLAMENCO_DIR=$(find_module flamenco)
SVNMAN_DIR=$(find_module svnman)
SDK_DIR=$(find_module pillarsdk)

echo "Pillar  : $PILLAR_DIR"
echo "Attract : $ATTRACT_DIR"
echo "Flamenco: $FLAMENCO_DIR"
echo "SVNMan  : $SVNMAN_DIR"
echo "SDK     : $SDK_DIR"

if [ -z "$PILLAR_DIR" -o -z "$ATTRACT_DIR" -o -z "$FLAMENCO_DIR" -o -z "$SVNMAN_DIR" -o -z "$SDK_DIR" ];
then
    exit 1
fi

function git_clone() {
    PROJECT_NAME="$1"
    BRANCH="$2"
    LOCAL_ROOT="$3"

    echo "==================================================================="
    echo "CLONING REPO ON $PROJECT_NAME @$BRANCH"
    URL=$(git -C $LOCAL_ROOT remote get-url origin)
    git -C $STAGINGDIR clone --depth 1 --branch $BRANCH $URL $PROJECT_NAME
}

if [ "$STAGING_BRANCH" == "production" ]; then
    SDK_STAGING_BRANCH=master  # SDK doesn't have a production branch
else
    SDK_STAGING_BRANCH=$STAGING_BRANCH
fi

git_clone pillar-python-sdk $SDK_STAGING_BRANCH $SDK_DIR
git_clone pillar $STAGING_BRANCH $PILLAR_DIR
git_clone attract $STAGING_BRANCH $ATTRACT_DIR
git_clone flamenco $STAGING_BRANCH $FLAMENCO_DIR
git_clone pillar-svnman $STAGING_BRANCH $SVNMAN_DIR
git_clone blender-cloud $STAGING_BRANCH $ROOT

# Gulp everywhere
GULP=$ROOT/node_modules/.bin/gulp
if [ ! -e $GULP -o gulpfile.js -nt $GULP ]; then
    npm install
    touch $GULP  # installer doesn't always touch this after a build, so we do.
fi

# List of projects
PROJECTS="pillar attract flamenco pillar-svnman blender-cloud"

# Run ./gulp for every project
for PROJECT in $PROJECTS; do
    pushd $STAGINGDIR/$PROJECT; ./gulp --production; popd;
done

# Remove node_modules (only after all projects with interdependencies have been built)
for PROJECT in $PROJECTS; do
    pushd $STAGINGDIR/$PROJECT; rm -r node_modules; popd;
done

echo
echo "==================================================================="
echo "Staging of ${PROJECT_NAME} is ready for dockerisation."
echo "==================================================================="
