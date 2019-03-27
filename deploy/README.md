# Deploying to Production

```
workon blender-cloud  # activate your virtualenv
cd $projectdir/deploy
./full-pull.sh
```

## The Details

Deployment consists of a few steps:

1. Populate a staging directory with the files from the production branches of the various projects.
2. Create Docker images.
3. Push the docker images to Docker Hub.
4. Pull the docker images on the production server and rebuild+restart the containers.

The scripts involved are:

- `2docker.sh`: performs step 1. above.
- `build-{xxx}.sh`: performs steps 2. and 3. above.
- `2server.sh`: performs step 4. above.

The `full-{xxx}.sh` scripts perform all the steps, and call into `build-{xxx}.sh`.

For `xxx` there are:

- `all`: Rebuild all Docker images from scratch. This is good for getting the latest updates to the
  base image.
- `pull`: Pull the base and intermediate images from Docker Hub so that they are the same as the
  last time someone pushed to production, then rebuilds the final Docker image.
- `quick`: Just rebuild the final Docker image. Only use this if the last time a deployment to
  the production server was done was by you, on the machine you're working on now.


## Hacking Stuff

To deploy another branch than `production`, do `export DEPLOY_BRANCH=otherbranch` before starting
the above commands.
