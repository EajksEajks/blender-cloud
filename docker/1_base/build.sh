#!/usr/bin/env bash

# Uses --no-cache to always get the latest upstream (security) upgrades.
exec docker build --no-cache "$@" -t pillar_base -f base.docker .
