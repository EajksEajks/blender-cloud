#!/usr/bin/env bash

if [ ! -f /installed ]; then
    echo "Installing pillar and pillarskd"
    # . /data/venv/bin/activate && pip install -e /data/git/pillar
    ln -s /data/git/pillar/pillar /data/venv/lib/python2.7/site-packages/pillar
    # . /data/venv/bin/activate && pip install -e /data/git/pillar-python-sdk
    ln -s /data/git/pillar-python-sdk/pillarsdk /data/venv/lib/python2.7/site-packages/pillarsdk
    touch installed
fi

if [ "$DEV" = "true" ]; then
    echo "Running in development mode"
    bash manage.sh runserver --host='0.0.0.0'
else
    # Run Apache
    a2enmod rewrite
    /usr/sbin/apache2ctl -D FOREGROUND
fi
