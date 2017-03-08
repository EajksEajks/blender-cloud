#!/usr/bin/env bash

set -e
cd /data/git/blender-cloud
exec python manage.py "$@"
