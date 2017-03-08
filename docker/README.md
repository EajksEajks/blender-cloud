# Setting up a production machine

To get the docker stack up and running, we use the following, on an Ubuntu 16.10 machine.

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
2. Edit the `[Service]` section of `/lib/systemd/system/docker.service`:
    1. Add `EnvironmentFile=/etc/default/docker`
    2. Append ` $DOCKER_OPTS` to the `ExecStart` line
3. Run `systemctl daemon-reload`
4. Remove all your containers and images.
5. Restart Docker: `systemctl restart docker`

## 3. Pull the Blender Cloud docker image

`docker pull armadillica/blender_cloud:latest-py36`

## 4. Get docker-compose + our repositories

See the [Quick setup](../README.md) on how to get those. Then run:

    cd /data/git/blender-cloud/docker
    docker-compose up -d

## 5. Set up TLS

Place TLS certificates in `/data/certs/{cloud,cloudapi}.blender.org.pem`.
They should contain (in order) the private key, the host certificate, and the
CA certificate.

## 6. Create a local config

Blender Cloud expects a file `/data/git/blender_cloud/config_local.py` to exist,
with machine-local configuration overrides.
