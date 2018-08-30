FROM ubuntu:18.04
LABEL maintainer="Sybren A. Stüvel <sybren@blender.studio>"

RUN set -ex; \
    apt-get update; \
    DEBIAN_FRONTEND=noninteractive apt-get install \
      -qyy -o APT::Install-Recommends=false -o APT::Install-Suggests=false \
      tzdata openssl ca-certificates locales; \
    locale-gen en_US.UTF-8 en_GB.UTF-8 nl_NL.UTF-8
ENV LANG en_US.UTF-8
