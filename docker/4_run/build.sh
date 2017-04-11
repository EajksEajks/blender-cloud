#!/usr/bin/env bash

exec docker build -t armadillica/blender_cloud:latest -f run.docker .
