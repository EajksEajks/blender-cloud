#!/bin/bash -e

docker build -t armadillica/blender_cloud:latest -f run.docker .

echo "Done, built armadillica/blender_cloud:latest"
