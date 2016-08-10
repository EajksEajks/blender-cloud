#!/usr/bin/env bash

mkdir -p ../3_run/wheelhouse;
cp ../../requirements.txt .;

docker build -t pillar_build -f build.docker .;
docker run --rm \
       -v "$(pwd)"/../3_run/wheelhouse:/data/wheelhouse \
       pillar_build;

rm requirements.txt;
