#!/bin/bash -e

BACKUPDIR=/data/storage/db-bak
DATE=$(date +'%Y-%m-%d-%H%M')
ARCHIVE=$BACKUPDIR/mongo-live-$DATE.tar.xz

# Just a sanity check before we give it to 'rm -rf'
if [ -z "$DATE" ]; then
    echo "Empty string found where the date should be, aborting."
    exit 1
fi


# /data/db-bak in Docker is /data/storage/db-bak on the host.
docker exec mongo mongodump -d cloud \
    --out /data/db-bak/dump-$DATE \
    --excludeCollection tokens \
    --excludeCollection flamenco_task_logs \
    --quiet

cd $BACKUPDIR
tar -Jcf $ARCHIVE dump-$DATE/
rm -rf dump-$DATE

TO_DELETE="$(ls $BACKUPDIR/mongo-live-*.tar.xz | head -n -7)"
[ -z "$TO_DELETE" ] || rm "$TO_DELETE"

rsync -a $BACKUPDIR/mongo-live-*.tar.xz cloud-backup@swami-direct.blender.cloud:
