# Blender Cloud

Welcome to the [Blender Cloud](https://cloud.blender.org/) code repo!
Blender Cloud runs on the [Pillar](https://pillarframework.org/) framework.

## Quick setup
Set up a node with these commands.

```
#!/usr/bin/env bash

sudo mkdir -p /data/{git,storage,config,certs}
sudo apt-get update
sudo apt-get -y install python3-pip
pip3 install docker-compose

cd /data/git
git clone git://git.blender.org/pillar-python-sdk.git
git clone git://git.blender.org/pillar.git -b production
git clone git://git.blender.org/attract.git -b production
git clone git://git.blender.org/flamenco.git -b production
git clone git://git.blender.org/blender-cloud.git -b production
git clone https://github.com/armadillica/grafista.git -b production

echo '0 8 * * * root docker exec -d grafista bash manage.sh collect' > /etc/cron.d/grafista

```

After these commands, run `deploy.sh` to build the static files and deploy
those too (see below).


## Preparing the production branch for deployment

All revisions to deploy to production should be on the `production` branches of all the relevant
repositories.

Make sure you have these aliases in the `[alias]` section of your `~/.gitconfig`:

```
prod = "!git checkout production && git fetch origin production && gitk --all"
ff = "merge --ff-only"
```

The following commands should be executed for each (sub)project; specifically for
the current repository, Pillar, Attract, Flamenco, and Pillar-SVNMan:

```
cd $projectdir

# Ensure there are no local, uncommitted changes.
git status
git stash  # if you still have local stuff.

# pull from master, run unittests, push your changes to master.
git pull
py.test
git push

# Switch to production branch, and investigate the situation.
git prod

# Fast-forward the production branch to the master branch.
git ff master

# Run tests again
py.test

# Push the production branch.
git push
```

## Deploying to production server

```
workon blender-cloud  # activate your virtualenv
cd $projectdir/deploy
./2docker.sh
cd $projectdir/docker
./full_rebuild.sh  # or one of the other build scripts, if you know what you're doing.
docker push armadillica/blender_cloud:latest
cd $projectdir/deploy
./2server.sh
```

To deploy another branch than `production`, do `export DEPLOY_BRANCH=otherbranch` before starting
the above commands.
