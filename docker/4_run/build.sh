#!/usr/bin/env bash

exec docker build -t armadillica/blender_cloud:latest-py36 -f run.docker .
