#!/bin/bash -e

# When updating this, also update the versions in Dockerfile-*, and make sure that
# it matches the versions of the elasticsearch and elasticsearch_dsl packages
# used in Pillar. Those don't have to match exactly, but the major version should.
VERSION=6.1.1

docker build -t armadillica/elasticsearch:${VERSION} -f Dockerfile-elastic .
docker build -t armadillica/kibana:${VERSION} -f Dockerfile-kibana .

docker tag armadillica/elasticsearch:${VERSION} armadillica/elasticsearch:latest
docker tag armadillica/kibana:${VERSION} armadillica/kibana:latest

echo "Done, built armadillica/elasticsearch:${VERSION} and armadillica/kibana:${VERSION}"
echo "Also tagged as armadillica/elasticsearch:latest and armadillica/kibana:latest"
