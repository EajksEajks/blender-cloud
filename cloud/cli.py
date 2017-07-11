#!/usr/bin/env python

import logging
from flask import current_app
from flask_script import Manager

from pillar.cli import manager
from pillar.api import service

log = logging.getLogger(__name__)

manager_cloud = Manager(
    current_app, usage="Blender Cloud scripts")


@manager_cloud.command
def create_groups():
    """Creates the admin/demo/subscriber groups."""

    import pprint

    group_ids = {}
    groups_coll = current_app.db('groups')

    for group_name in ['admin', 'demo', 'subscriber']:
        if groups_coll.find({'name': group_name}).count():
            log.info('Group %s already exists, skipping', group_name)
            continue
        result = groups_coll.insert_one({'name': group_name})
        group_ids[group_name] = result.inserted_id

    service.fetch_role_to_group_id_map()
    log.info('Created groups:\n%s', pprint.pformat(group_ids))


@manager_cloud.command
def reconcile_subscribers():
    """For every user, check their subscription status with the store."""

    from pillar.api.blender_cloud.subscription import fetch_subscription_info

    service.fetch_role_to_group_id_map()

    users_coll = current_app.data.driver.db['users']
    unsubscribed_users = []
    found = users_coll.find({'roles': 'subscriber'})
    log.info('Processing %i users', found.count())

    for user in found:
        log.info('Processing %s' % user['email'])

        user_store = fetch_subscription_info(user['email'])
        if not user_store:
            log.error('Unable to reach store, aborting')
            break

        if not user_store or user_store['cloud_access'] == 0:
            action = 'revoke'
            unsubscribed_users.append(user['email'])
        else:
            action = 'grant'

        service.do_badger(action, 'subscriber', user_id=user['_id'])

    if not unsubscribed_users:
        log.info('No unsubscribed users')
        return

    print('The following users have been unsubscribed')
    for user in unsubscribed_users:
        print(user)


manager.add_command("cloud", manager_cloud)
