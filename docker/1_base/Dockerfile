FROM ubuntu:17.10
MAINTAINER Francesco Siddi <francesco@blender.org>

RUN apt-get update && apt-get install -qyy \
    -o APT::Install-Recommends=false -o APT::Install-Suggests=false \
    openssl ca-certificates
