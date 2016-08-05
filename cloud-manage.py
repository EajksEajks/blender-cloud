#!/usr/bin/env python

from pillar import cli
from cloud import app

cli.manager.app = app
cli.manager.run()
