# Blender Cloud

Welcome to the [Blender Cloud](https://cloud.blender.org/) code repo!
Blender Cloud runs on the [Pillar](https://pillarframework.org/) framework.

## Development setup
Jumpstart Blender Cloud development with this simple guide.

### System setup
Blender Cloud relies on a number of services in order to run. Check out the [Pillar system setup](
https://pillarframework.org/development/system_setup/#step-by-step-setup) to set this up.

### Check out the code
Go to the local development directory and check out the following repositories, next to each other.

```
cd /home/guest/Developer
git clone git://git.blender.org/pillar-python-sdk.git
git clone git://git.blender.org/pillar.git
git clone git://git.blender.org/attract.git
git clone git://git.blender.org/flamenco.git
git clone git://git.blender.org/pillar-svnman.git
git clone git://git.blender.org/blender-cloud.git
```

### Initial setup and configuration

Switch to the (previously created) virtualenv for the project and install the requirements:

```
cd /home/guest/Developer/blender-cloud
workon blender-cloud
pip install -r requirements-dev.txt
```

Build assets and templates for all Blender Cloud dependencies using Gulp.

```
./gulp all
```

Make a copy of the config_local example, which will be further edited as the application is
configured.

```
cp config_local.example.py config_local.py
```

Setup the database with the initial collections and the admin user.

```
./manage.py setup setup_db your_email
```

The command will return the following message:

```
Created project <project_id> for user <user_id>
```

Copy the value of `<project_id>` and assign it as value for `MAIN_PROJECT_ID`.


## Development

When ready to commit, change the remotes to work over SSH. For example:

`git remote set-url origin git@git.blender.org:blender-cloud.git`

For more information, check out [this guide](https://wiki.blender.org/wiki/Tools/Git#Commit_Access).


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
./build-all.sh  # or ./build-quick.sh
./2server.sh servername
```

To deploy another branch than `production`, do `export DEPLOY_BRANCH=otherbranch` before starting
the above commands.
