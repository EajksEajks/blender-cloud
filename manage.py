#!/usr/bin/env python

import logging
from flask import current_app
from pillar import cli
from pillar.cli import manager_maintenance
from cloud import app

log = logging.getLogger(__name__)


@manager_maintenance.command
def reconcile_subscribers():
    """For every user, check their subscription status with the store."""
    from pillar.auth.subscriptions import fetch_user

    users_coll = current_app.data.driver.db['users']
    unsubscribed_users = []
    for user in users_coll.find({'roles': 'subscriber'}):
        print('Processing %s' % user['email'])
        print('  Checking subscription')
        user_store = fetch_user(user['email'])
        if user_store['cloud_access'] == 0:
            print('    Removing subscriber role')
            users_coll.update(
                {'_id': user['_id']},
                {'$pull': {'roles': 'subscriber'}})
            unsubscribed_users.append(user['email'])

    if not unsubscribed_users:
        return

    print('The following users have been unsubscribed')
    for user in unsubscribed_users:
        print(user)

cli.manager.app = app
cli.manager.run()
