#!/bin/bash -e

docker build -t armadillica/elasticsearch:latest -f Dockerfile-elastic .
docker build -t armadillica/kibana:latest -f Dockerfile-kibana .

echo "Done, built armadillica/elasticsearch:latest and armadillica/kibana:latest"
