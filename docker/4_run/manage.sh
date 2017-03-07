#!/usr/bin/env bash -e

. /data/venv/bin/activate
cd /data/git/blender-cloud
python manage.py "$@"
