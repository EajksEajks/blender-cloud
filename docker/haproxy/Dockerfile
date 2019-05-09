FROM dockercloud/haproxy:1.6.7
LABEL maintainer="Sybren A. Stüvel <sybren@blender.studio>"

# Fix https://talosintelligence.com/vulnerability_reports/TALOS-2019-0782
RUN sed 's/root::/root:!:/' -i /etc/shadow
