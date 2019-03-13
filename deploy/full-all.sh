#!/bin/bash

set -e

NAME="$(basename "$0")"

./2docker.sh
./${NAME/full-/build-}
./2server.sh cloud2
