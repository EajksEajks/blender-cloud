# Blender Cloud

Welcome to the [Blender Cloud](https://cloud.blender.org) code repo!
Blender Cloud runs on the [Pillar](https://pillarframework.org) framework.

## Quick setup
Set up a node with these commands. Note that that script is already outdated...

```
#!/usr/bin/env bash

mkdir -p /data/git
mkdir -p /data/storage
mkdir -p /data/config
mkdir -p /data/certs

sudo apt-get update
sudo apt-get -y install python-pip
pip install docker-compose

cd /data/git
git clone git://git.blender.org/pillar-python-sdk.git
git clone git://git.blender.org/pillar-server.git pillar
git clone git://git.blender.org/attract.git
git clone git://git.blender.org/blender-cloud.git
```

## Deploying to production server

First of all, add those aliases to the `[alias]` section of your `~/.gitconfig`

```
prod = "!git checkout production && git fetch origin production && gitk --all"
ff = "merge --ff-only"
pp = "!git push && if [ -e deploy.sh ]; then ./deploy.sh; fi && git checkout master"
```

The following commands should be executed for each subproject; specifically for
Pillar and Attract:

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

# Push the production branch and run dummy deploy script.
git pp  # pp = "Push to Production"

# The above alias waits for [ENTER] until all deploys are done.
# Let it wait, perform the other commands in another terminal.
```

Now follow the above receipe on the Blender Cloud project as well.
Contrary to the subprojects, `git pp` will actually perform the deploy
for real.

Now you can press `[ENTER]` in the Pillar and Attract terminals that
were still waiting for it.

After everything is done, your (sub)projects should all be back on
the master branch.
