#!/usr/bin/env bash

set -x;
set -e;

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $DIR;

cd 1_base/;
bash build.sh;

cd ../2_build/;
bash build.sh;

cd ../3_run/;
bash build.sh;
