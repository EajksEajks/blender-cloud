#!/usr/bin/env bash

set -e
cd /data/topdev/blender-cloud
source /data/venv/bin/activate
pip wheel --wheel-dir=/data/wheelhouse -r requirements.txt
