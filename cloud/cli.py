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

    import threading
    import concurrent.futures
    from pillar.api.blender_cloud.subscription import fetch_subscription_info

    service.fetch_role_to_group_id_map()

    users_coll = current_app.data.driver.db['users']
    unsubscribed_users = []
    found = users_coll.find({'roles': 'subscriber'})
    user_count = found.count()
    log.info('Processing %i users', user_count)

    lock = threading.Lock()

    real_current_app = current_app._get_current_object()

    def do_user(idx, user):
        log.info('Processing %i/%i %s', idx + 1, user_count, user['email'])

        with real_current_app.app_context():
            user_store = fetch_subscription_info(user['email'])

            if not user_store:
                log.error('Unable to reach store, aborting')
                return

            if not user_store or user_store['cloud_access'] == 0:
                action = 'revoke'
                with lock:
                    unsubscribed_users.append(user['email'])
            else:
                action = 'grant'

            with lock:
                service.do_badger(action, role='subscriber', user_id=user['_id'])

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        future_to_user = {executor.submit(do_user, idx, user): user
                          for idx, user in enumerate(found)}
        for future in concurrent.futures.as_completed(future_to_user):
            user = future_to_user[future]
            try:
                future.result()
            except Exception as ex:
                log.exception('Error updating user %s', user)

    if not unsubscribed_users:
        log.info('No unsubscribed users')
        return

    print('The following %i users have been unsubscribed' % len(unsubscribed_users))
    for user in unsubscribed_users:
        print(user)


manager.add_command("cloud", manager_cloud)
