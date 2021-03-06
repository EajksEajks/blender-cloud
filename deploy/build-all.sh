#!/bin/bash -e

# macOS does not support readlink -f, so we use greadlink instead
if [[ `uname` == 'Darwin' ]]; then
    command -v greadlink 2>/dev/null 2>&1 || { echo >&2 "Install greadlink using brew."; exit 1; }
    readlink='greadlink'
else
    readlink='readlink'
fi
ROOT="$(dirname "$(dirname "$($readlink -f "$0")")")"

case "$(basename "$0")" in
    build-pull.sh)
        docker pull armadillica/pillar_py:3.6
        docker pull armadillica/pillar_wheelbuilder:latest
        pushd "$ROOT/docker/3_buildwheels"
        ./build.sh
        popd
        pushd "$ROOT/docker/4_run"
        ./build.sh
        ;;
    build-quick.sh)
        pushd "$ROOT/docker/4_run"
        ./build.sh
        ;;
    build-all.sh)
        pushd "$ROOT/docker"
        ./full_rebuild.sh
        ;;
    *)
        echo "Unknown script $0, aborting" >&2
        exit 1
esac

popd
echo
echo "Press [ENTER] to push the new Docker images."
read dummy
docker push armadillica/pillar_py:3.6
docker push armadillica/pillar_wheelbuilder:latest
docker push armadillica/blender_cloud:latest
echo
echo "Build is done, ready to update the server."
