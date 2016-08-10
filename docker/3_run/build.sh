#!/usr/bin/env bash

cp ../../requirements.txt .;
docker build -t armadillica/blender_cloud -f run.docker .;
rm requirements.txt;
