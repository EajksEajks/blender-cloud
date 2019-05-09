#!/bin/bash -e

# When updating this, also update the version in Dockerfile
VERSION=1.6.7

docker build -t armadillica/haproxy:${VERSION} .
docker tag armadillica/haproxy:${VERSION} armadillica/haproxy:latest

echo "Done, built armadillica/haproxy:${VERSION}"
echo "Also tagged as armadillica/haproxy:latest"
