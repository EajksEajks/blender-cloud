# Setting up a production machine

To get the docker stack up and running, we use the following, on an Ubuntu 16.10 machine.

## 0. Basic stuff

Install the machine, use `locale-gen nl_NL.UTF-8` or similar commands to generate locale
definitions. Set up automatic security updates and backups, the usual.

## 1. Install Docker

Install Docker itself, as described in the
   [Docker CE for Ubuntu manual](https://store.docker.com/editions/community/docker-ce-server-ubuntu?tab=description):

    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable"
    apt-get update
    apt-get install docker-ce

## 2. Configure Docker to use "overlay"

Configure Docker to use "overlay" instead of "aufs" for the images. This prevents
[segfaults in auplink](https://bugs.launchpad.net/ubuntu/+source/aufs-tools/+bug/1442568).

1. Set `DOCKER_OPTS="-s overlay"` in `/etc/defaults/docker`
2. Copy `/lib/systemd/system/docker.service` to `/etc/systemd/system/docker.service`.
   This allows later upgrading of docker without overwriting the changes we're about to do.
2. Edit the `[Service]` section of `/etc/systemd/system/docker.service`:
    1. Add `EnvironmentFile=/etc/default/docker`
    2. Append ` $DOCKER_OPTS` to the `ExecStart` line
3. Run `systemctl daemon-reload`
4. Remove all your containers and images.
5. Restart Docker: `systemctl restart docker`

## 3. Pull the Blender Cloud docker image

`docker pull armadillica/blender_cloud:latest`

## 4. Get docker-compose + our repositories

See the [Quick setup](../README.md) on how to get those. Then run:

    cd /data/git/blender-cloud/docker
    docker-compose up -d


Set up permissions for Docker volumes; the following should be writable by

- `/data/storage/pillar`: writable by `www-data` and `root` (do a `chown root:www-data`
  and `chmod 2770`).
- `/data/storage/db`: writable by uid 999.


## 5. Set up TLS

Place TLS certificates in `/data/certs/{cloud,cloudapi}.blender.org.pem`.
They should contain (in order) the private key, the host certificate, and the
CA certificate.

## 6. Create a local config

Blender Cloud expects the following files to exist:

- `/data/git/blender_cloud/config_local.py` with machine-local configuration overrides
- `/data/config/google_app.json` with Google Cloud Storage credentials.


## 7. ElasticSearch & kibana

ElasticSearch and Kibana run in our self-rolled images. This is needed because by default

- ElasticSearch uses up to 2 GB of RAM, which is too much for our droplet, and
- the Docker images contain the proprietary X-Pack plugin, which we don't want.

This also gives us the opportunity to let Kibana do its optimization when we build the image, rather
than every time the container is recreated.

`/data/storage/elasticsearch` needs to be writable by UID 1000, GID 1000.

Kibana connects to [ElasticProxy](https://github.com/armadillica/elasticproxy), which only allows
GET, HEAD, and some specific POST requests. This ensures that the public-facing Kibana cannot be
used to change the ElasticSearch database.

Production Kibana can be placed in read-only mode, but this is not necessary now that we use
ElasticProxy. However, I've left this in here as reference.

`curl -XPUT 'localhost:9200/.kibana/_settings' -d '{ "index.blocks.read_only" : true }'`

If editing is desired, temporarily turn off read-only mode:

`curl -XPUT 'localhost:9200/.kibana/_settings' -d '{ "index.blocks.read_only" : false }'`
